import asyncio
import json
import logging
import shutil
import subprocess
from json import load
from pathlib import Path
from xml.etree.ElementTree import ParseError

import PySimpleGUI as sg

from t9a.pdf import get_version_from_PDF, match_titles, export_titles_to_json
from t9a.sla import SLAFile
from t9a import T9A_ICON


SETTINGS_FILE = Path(__file__).parent / "lab_manager/t9a_lab_manager_settings.json"
CURRENT_LABS = ["ID", "WDG", "DL", "UD", "SE"]

logging.basicConfig(level=logging.INFO)


async def compare_rules(pdf1, pdf2):
    return await asyncio.run(match_titles(pdf1, pdf2))

# TODO: Check number of rules frames against PDF page count to see if manual changes needed


def copy_file(file: Path, directory: Path):
    destination = directory / file.name
    logging.info(f"Copying {file} to {destination}")
    try:
        shutil.copy(file, destination)
    except shutil.SameFileError:
        logging.debug("Old file and new file are the same")
    return destination


def get_settings():
    if Path(SETTINGS_FILE).is_file():
        with open(SETTINGS_FILE) as json_file:
            return json.load(json_file)
    else:
        entries = [{"name": lab, "filename": None} for lab in CURRENT_LABS]
        settings = {"labs": entries}
        with open(SETTINGS_FILE, "w") as json_file:
            json.dump(settings, json_file, indent=4)
    return settings


def update_settings_list(settings, list):
    lab_list = [{"name": entry[0], "filename":entry[1]} for entry in list]
    settings['labs'] = lab_list
    with open(SETTINGS_FILE, "w") as json_file:
        json.dump(settings, json_file, indent=4)


def open_scribus(filename=None):
    if scribus_exe := shutil.which("scribus"):
        subprocess.Popen([scribus_exe, "--console", filename])
    else:
        sg.popup_ok("Couldn't launch Scribus. Is it installed and is the scribus executable on your PATH?",
                    title="Couldn't launch Scribus")


def main():  # sourcery skip: use-fstring-for-concatenation
    sg.theme('Dark Blue 14')
    settings = get_settings()
    lab_list = [[lab['name'], lab['filename']] for lab in settings['labs']]

    file_list_column = [
        [sg.Text("Favourites")],
        [sg.Table(lab_list, enable_events=True, expand_x=True, key="-FILE-LIST-",
                  headings=["Army", "Filename"], col_widths=[5, 40],
                  justification="left", select_mode=sg.TABLE_SELECT_MODE_BROWSE,
                  num_rows=10, expand_y=True)],
        [sg.Button("+", size=2, key="-ADD-NEW-"),
         sg.Button("–", size=2, key="-DELETE-SELECTED-"),
         sg.Push(), sg.Button("Edit", key="-EDIT-SELECTED-")]
    ]

    tools_column = [
        [sg.Frame("Scribus File", [
            [sg.In(size=50, key='-FILE-', enable_events=True),
             sg.FileBrowse(target='-FILE-', file_types=(("SLA Files", "*.sla"),)),],
            [sg.Button("Open in Scribus", key="-OPEN-SCRIBUS-", disabled=True, size=13),
             sg.Button("Check",key="-CHECK-SLA-",disabled=True)]])],
        [sg.Frame("Embedded Rules", [
            [sg.In(size=(50, 1), key="-RULES-", expand_x=True, readonly=True)],
            [sg.Button("Open", key="-OPEN-OLD-RULES-", disabled=True,),
             sg.Button("Parse", key="-PARSE-PDF-", disabled=True,),
             sg.Text("Version:"), sg.Text(key="-OLD-VERSION-", relief=sg.RELIEF_GROOVE, border_width=1, expand_x=True)],
        ], expand_x=True)],
        [sg.Frame("New Rules", [
            [sg.In(size=50, key='-NEW-RULES-', visible=True, enable_events=True),
             sg.FileBrowse(target='-NEW-RULES-',file_types=(("PDF Files", "*.pdf"),))],
            [sg.Button("Open", key="-OPEN-NEW-RULES-", disabled=True,),
             sg.Text("Version:"), sg.Text(key='-NEW-VERSION-', relief=sg.RELIEF_GROOVE, border_width=1, expand_x=True)],
        ])],
        [sg.Frame("Compare and Replace", [
            [sg.Button("Compare", key="-COMPARE-", disabled=True),
             sg.Text("Result:"), sg.Text(key="-RESULT-", relief=sg.RELIEF_GROOVE, border_width=1, expand_x=True),
             sg.Button("Replace", key="-REPLACE-", disabled=True, button_color="red")],
        ], expand_x=True)],
        [sg.Button("Select Files for Export…", key="-EXPORT-MENU-")],
    ]

    # Full layout
    layout = [
        [
            sg.Col(file_list_column, vertical_alignment="top", expand_x=True, expand_y=True,),
            sg.Col(tools_column, vertical_alignment="top")
        ]
    ]

    window = sg.Window("T9A LAB Details", layout, resizable=True, icon=T9A_ICON, titlebar_icon=T9A_ICON)
    filename = None
    new_pdf = None

    def add_edit_file(entry=None):

        add_edit_layout = [
            [
                sg.Text("Army", size=10),
                sg.In(size=(20, 1), key="-NEW-NAME-"),
            ],
            [
                sg.Text("Filename", size=10),
                sg.In(size=(60, 1), key="-NEW-FILE-"),
                sg.FileBrowse(file_types=(("SLA Files", "*.sla"),))
            ],
            [sg.Button('OK', key="-SUBMIT-")]
        ]

        title = "Edit File" if entry else "New File"
        window = sg.Window(title, add_edit_layout, use_default_focus=False, finalize=True, modal=True)

        if entry:
            window['-NEW-NAME-'].update(entry[0])
            window['-NEW-FILE-'].update(entry[1])
        event, values = window.read()
        if values:
            result = [values['-NEW-NAME-'], values['-NEW-FILE-']]
            window.close()
            return result

    def export_menu():
        quality_options = [
            [sg.Checkbox("High", default=True, key="-o-high-")],
            [sg.Checkbox("Low", default=True, key="-o-low-")],
            [sg.Checkbox("Print", default=False, key="-o-print-")],
        ]
        format_options = [
            [sg.Checkbox("Full", default=True, key="-o-full-")],
            [sg.Checkbox("No Points", default=True, key="-o-nopoints-")],
            [sg.Checkbox("No Rules", default=False, key="-o-norules-")],
        ]
        export_panel = [
            [sg.Text("Select export options")],
            [
                sg.Frame("Quality", quality_options, expand_x=True),
                sg.Frame("Format", format_options, expand_x=True)
            ],
            [
                sg.Frame("Options", [
                    [sg.Checkbox("Do not export (PDFs already created)", default=False, key="-o-noexport-")],
                    [sg.Checkbox("Do not post-process (bookmarks, renaming, moving)", default=False, key="-o-noprocess-")],
                ]),
            ],
            [sg.Text("Destination folder:")],
            [
                sg.In(size=50, key='-OUT-DIR-'),
                sg.FolderBrowse(),
            ],
            [
                sg.Push(),
                sg.Button("Export", key="-EXPORT-BUTTON-",
                          button_color="red"),
                sg.Push(),
            ],

        ]
        export_list = [
            [sg.Text("Select one or more (Ctrl+Click) files to export from Scribus:")],
            [
                sg.Table(lab_list, enable_events=False, expand_x=True, expand_y=True, key="-FILE-LIST-", headings=["Army", "Filename"], auto_size_columns=False,
                         col_widths=[5, 40], justification="left", select_mode=sg.TABLE_SELECT_MODE_EXTENDED),
            ]
        ]
        export_layout = [
            [
                sg.Col(export_list, vertical_alignment="top",
                       expand_x=True, expand_y=True,),
                sg.Col(export_panel, vertical_alignment="top")
            ]
        ]
        window = sg.Window("Export LABs", export_layout,
                           use_default_focus=False, finalize=True, modal=True)
        while True:
            event, values = window.read()
            match event:
                case "Exit" | sg.WIN_CLOSED:
                    break

                case "-EXPORT-BUTTON-":
                    selected_files = [lab_list[entry][1] for entry in values["-FILE-LIST-"]]
                    qualities = []
                    formats = []
                    if values["-o-high-"]:
                        qualities.append("high")
                    if values["-o-low-"]:
                        qualities.append("low")
                    if values["-o-print-"]:
                        qualities.append("print")
                    if values["-o-full-"]:
                        formats.append("full")
                    if values["-o-nopoints-"]:
                        formats.append("nopoints")
                    if values["-o-norules-"]:
                        formats.append("norules")

                    # TODO: preflight selected files
                    for file in selected_files:
                        lab = SLAFile(file)
                        if "nopoints" in formats and not lab.check_nopoints():
                            sg.popup_ok(f"Couldn't find nopoints version of the rules for file: {file}. Please make sure _nopoints PDF is in the images folder.")
                            return

                    logging.info(selected_files)
                    logging.info(qualities)
                    logging.info(formats)
                    file_list = ""
                    for file in selected_files:
                        file_list += f'"{file}" '
                    logging.info(file_list)
                    flags = []
                    if values["-o-noexport-"]:
                        flags.append("--noexport")
                    if values["-o-noprocess-"]:
                        flags.append("--noprocess")
                    if values["-OUT-DIR-"]:
                        dest = f"--dest {values['-OUT-DIR-']}"
                    else:
                        dest = ""
                    # TODO: full path for generate script
                    command = sg.execute_command_subprocess(
                        "python",
                        "t9a_generate_labs.py",
                        file_list,
                        "--quality",
                        ' '.join(qualities),
                        "--formats",
                        ' '.join(formats),
                        ' '.join(flags),
                        dest,
                        pipe_output=True,
                    )
                    logging.info(sg.execute_get_results(command)[0])

        window.close()

    def load_file(filename):
        try:
            lab = SLAFile(filename)
            window["-FILE-"].update(filename)
            window["-OPEN-SCRIBUS-"].update(disabled=False)
            window["-OPEN-OLD-RULES-"].update(disabled=False)
            window["-PARSE-PDF-"].update(disabled=False)
            window["-CHECK-SLA-"].update(disabled=False)
            window["-RULES-"].update("...")
            rules_pdf = lab.get_embedded_rules()
            window["-RULES-"].update(rules_pdf)
            window["-OLD-VERSION-"].update(get_version_from_PDF(rules_pdf))
        except ParseError as e:
            window["-FILE-"].update("Not a valid .sla file")
            disable_load()
            return
        except Exception as e:
            logging.debug(e)
            window["-RULES-"].update("Error")
        return lab

    def disable_load():
        window["-OPEN-SCRIBUS-"].update(disabled=True)
        window["-OPEN-OLD-RULES-"].update(disabled=True)
        window["-RULES-"].update("")
        window["-OLD-VERSION-"].update("")

    while True:
        event, values = window.read()
        match event:

            case "Exit" | sg.WIN_CLOSED:
                break

            case "-FILE-":
                filename = Path(values["-FILE-"])
                lab = load_file(filename)

            case "-FILE-LIST-":
                if values[event]:
                    data_selected = [lab_list[row] for row in values[event]]
                    # filename = values['-FILE-LIST-'][0][1]
                    # if filename := Path(data_selected[0][1]):
                    if data_selected[0][1]:
                        filename = Path(data_selected[0][1])
                        if filename.is_file():
                            # window["-FILE-"].update(filename)
                            lab = load_file(filename)
                        else:
                            window["-FILE-"].update("No valid file selected")
                            disable_load()

            case "-NEW-RULES-":
                new_pdf = Path(values["-NEW-RULES-"])
                window['-NEW-RULES-'].update(new_pdf)
                try:
                    new_rules_version = get_version_from_PDF(new_pdf)
                except:
                    new_rules_version = "ERROR"
                window["-NEW-VERSION-"].update(new_rules_version)
                window["-COMPARE-"].update(disabled=False)
                window["-REPLACE-"].update(disabled=False)
                window["-OPEN-NEW-RULES-"].update(disabled=False)

            case "-COMPARE-":
                rules_pdf = window["-RULES-"].get()
                if not filename or not new_pdf:
                    window['-RESULT-'].update("No file selected")
                    continue
                window['-RESULT-'].update("Matching...")

                try:
                    # TODO: parrallelise
                    match = match_titles(rules_pdf, new_pdf)
                    if match:
                        window['-RESULT-'].update(
                            'Titles match!',
                            text_color="white",
                            background_color="green",
                        )

                    else:
                        window['-RESULT-'].update(
                            'Titles do not match!',
                            text_color="white",
                            background_color="red",
                        )

                except:
                    window['-RESULT-'].update('ERROR')

            case "-REPLACE-":
                # nopoints = os.path.splitext(new_pdf)[0] + '_nopoints.pdf'
                nopoints = new_pdf.parent / (new_pdf.stem + '_nopoints.pdf')
                new_pdf = copy_file(new_pdf, filename.parent / 'images')
                logging.debug(f"checking for nopoints version: {nopoints}")
                if nopoints.is_file():
                    logging.debug(f"Copying to: {new_pdf.parent / 'images'}")
                    copy_file(nopoints, new_pdf.parent)
                lab.replace_pdf(new_pdf)
                rules_pdf = lab.get_embedded_rules()
                window["-RULES-"].update(rules_pdf)
                new_version = window["-NEW-VERSION-"].get()
                lab.set_version(new_version)

            case "-OPEN-OLD-RULES-":
                subprocess.Popen(window['-RULES-'].get(), shell=True)

            case "-OPEN-NEW-RULES-":
                subprocess.Popen(str(new_pdf), shell=True)

            case "-ADD-NEW-":
                if new_file := add_edit_file():
                    lab_list.append(new_file)
                    window['-FILE-LIST-'].update(lab_list)
                    update_settings_list(settings, lab_list)

            case "-EDIT-SELECTED-":
                selected_row = values["-FILE-LIST-"][0]
                data_selected = lab_list[selected_row]
                if new_file := add_edit_file(data_selected):
                    lab_list[selected_row] = new_file
                    window['-FILE-LIST-'].update(lab_list)
                    update_settings_list(settings, lab_list)

            case "-DELETE-SELECTED-":
                selected_row = values["-FILE-LIST-"][0]
                lab_list.pop(selected_row)
                window['-FILE-LIST-'].update(lab_list)
                update_settings_list(settings, lab_list)

            case "-OPEN-SCRIBUS-":
                filename = Path(values["-FILE-"])
                logging.debug(f"opening {filename} in Scribus")
                open_scribus(filename)

            case "-EXPORT-MENU-":
                export_menu()

            case "-PARSE-PDF-":
                rules_pdf = Path(window["-RULES-"].get())
                # if filename and filename.is_file():
                #     json_file = filename.parent/(rules_pdf.stem+".json")
                # else:
                #     json_file = None
                json_file = rules_pdf.with_suffix(".json")
                logging.debug(f"Creating JSON file: {json_file}")
                export_titles_to_json(rules_pdf,json_file)
                window["-OLD-VERSION-"].update("Exported")

            case "-CHECK-SLA-":
                missing_frames = lab.test_frames()
                missing_styles = lab.test_styles()
                if missing_frames or missing_styles:
                    sg.popup_ok(f"Missing Frames: {missing_frames}\n\nMissing Styles: {missing_styles}")
                else:
                    sg.popup_ok("All expected frames and styles are present.")

    window.close()


main()
