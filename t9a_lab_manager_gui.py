from json import load
import subprocess
import PySimpleGUI as sg
import asyncio
from t9a.sla import LABfile
from t9a.pdf import match_titles, get_version_from_PDF
import json
from xml.etree.ElementTree import ParseError
import os.path
from pathlib import Path
import shutil
import subprocess

async def compare_rules(pdf1, pdf2):
    return await asyncio.run(match_titles(pdf1, pdf2))

SETTINGS_FILE = './lab_manager/t9a_lab_manager_settings.json'
CURRENT_LABS = ["ID", "WDG", "DL", "UD", "SE"]

from t9a_base64 import t9a_icon_base64 as T9A_ICON

# TODO: Check number of rules frames against PDF page count to see if manual changes needed

def copy_file(file,directory):
    destination = directory+'/'+os.path.basename(file)
    print(f"Copying {file} to {destination}")
    try:
        shutil.copy(file,destination)
    except shutil.SameFileError:
        print("Old file and new file are the same")
    return destination

def get_settings():
    if Path(SETTINGS_FILE).is_file():
        with open(SETTINGS_FILE) as json_file:
            return json.load(json_file)
    else:
        entries = [{"name":lab,"filename":None} for lab in CURRENT_LABS ]
        settings = {"labs":entries}
        with open(SETTINGS_FILE,"w") as json_file:
            json.dump(settings, json_file, indent=4)
    return settings
    
def update_settings_list(settings,list):
    lab_list = [{"name":entry[0],"filename":entry[1]} for entry in list]
    settings['labs'] = lab_list
    with open(SETTINGS_FILE, "w") as json_file:
        json.dump(settings, json_file, indent=4)

def open_scribus(filename=None):
    if scribus_exe := shutil.which("scribus"):
        subprocess.Popen([scribus_exe,filename])
    else:
        sg.popup_ok("Couldn't launch Scribus. Is it installed and is the scribus executable on your PATH?",
                       title="Couldn't launch Scribus")

def main():

    sg.theme('Dark Blue 14')
    settings = get_settings()
    lab_list = [[lab['name'],lab['filename']] for lab in settings['labs']]

    file_list_column = [
        [
            sg.Text("Favourites"),
        ],
        [
            sg.Table(lab_list, enable_events=True, expand_x=True, key="-FILE-LIST-",headings=["Army","Filename"], auto_size_columns=False,
                            col_widths=[5,40], justification="left", select_mode=sg.TABLE_SELECT_MODE_BROWSE,num_rows=10,expand_y=True)
        ],
        [
            sg.Button("+", size=2, key="-ADD-NEW-"),
            sg.Button("–", size=2, key="-DELETE-SELECTED-"),
            sg.Push(),
            sg.Button("Edit", key="-EDIT-SELECTED-"),
        ]
    ]

    tools_column = [
        [
            sg.Frame("Scribus File", [
                [
                    # sg.Text("File:", size=10),
                    sg.In(size=50,key='-FILE-', enable_events=True),
                    sg.FileBrowse(target='-FILE-',
                                  file_types=(("SLA Files", "*.sla"),)),
                ],
                [
                    sg.Button("Open in Scribus",
                              key="-OPEN-SCRIBUS-", disabled=True, size=13)
                ],
            ])
        ],
        [
            sg.Frame("Embedded Rules", [
                [
                    # sg.Text("Filename:", size=10,),
                    sg.In(size=(50, 1), key="-RULES-", expand_x=True, readonly=True,)
                ],
                [
                    sg.Button("Open PDF", key="-OPEN-OLD-RULES-",
                              disabled=True, size=13),
                    sg.Text("Version:",),
                    sg.Text(key="-OLD-VERSION-",
                            relief=sg.RELIEF_GROOVE, border_width=1,expand_x=True),
                ],
            ], expand_x=True)
        ],
        [
            sg.Frame("New Rules", [
                [
                    # sg.Text("Select:",size=10),
                    sg.In(size=50,key='-NEW-RULES-', visible=True, enable_events=True),
                    sg.FileBrowse(target='-NEW-RULES-'),
                ],
                # [
                #     sg.Text("Filename:", size=10,),
                #     sg.In(size=40, key='-NEW-RULES-', enable_events=True),
                # ],
                [
                    sg.Button("Open PDF", key="-OPEN-NEW-RULES-",
                              disabled=True,size=13),
                    sg.Text("Version:",),
                    sg.Text(key='-NEW-VERSION-',
                            relief=sg.RELIEF_GROOVE, border_width=1, expand_x=True),
                ],

            ])
        ],
        # [sg.HorizontalSeparator()],
        [
            sg.Frame("Compare and Replace", [
                [
                    sg.Button("Compare", key="-COMPARE-", disabled=True),
                    sg.Text("Result:",),
                    sg.Text(key="-RESULT-", relief=sg.RELIEF_GROOVE,
                            border_width=1, expand_x=True),
                    # sg.Push(),
                    sg.Button("Replace", key="-REPLACE-",
                            disabled=True, button_color="red",),
                ],
            ],expand_x=True)
        ],
        # [sg.HorizontalSeparator()],
        [
            sg.Push(),
            sg.Button("Select Files for Export…", key="-EXPORT-MENU-",)
        ],

    ]


    # Full layout
    layout = [
        # [
        #     sg.Text("LAB .sla file"),
        #     sg.In(size=(60,1), enable_events=True, key="-FILE-",expand_x=True, readonly=True),
        #     sg.FileBrowse(file_types=(("SLA Files", "*.sla"),))
        # ],

        [
            sg.Col(file_list_column, vertical_alignment="top",expand_x=True, expand_y=True,),
            sg.Col(tools_column, vertical_alignment="top")
        ]
    ]

    window = sg.Window("T9A LAB Details", layout, resizable=True, icon=T9A_ICON, titlebar_icon=T9A_ICON)
    filename = None
    new_pdf = None


    def add_edit_file(entry=None):
        add_edit_layout = [
            [
                sg.Text("Army",size=10),
                sg.In(size=(20, 1), key="-NEW-NAME-"),
            ],
            [
                sg.Text("Filename",size=10),
                sg.In(size=(60, 1), key="-NEW-FILE-"),
                sg.FileBrowse(file_types=(("SLA Files", "*.sla"),))
            ],
            [sg.Button('OK', key="-SUBMIT-")]
        ]
        if entry:
            title = "Edit File"
            window['-NEW-NAME-'].update(entry[0])
            window['-NEW-FILE-'].update(entry[1])
        else:
            title = "New File"
        window = sg.Window(title, add_edit_layout, use_default_focus=False, finalize=True, modal=True)
        event, values = window.read()
        if values:
            result = [values['-NEW-NAME-'],values['-NEW-FILE-']]
            window.close()
            return result
        
    def export_menu():
        # TODO: Check for _nopoints.pdf files before exporting No Points version
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

                    # for entry in values["-FILE-LIST-"]:
                    #     selected_files.append(lab_list[entry][1])
                    print(selected_files)
                    print(qualities)
                    print(formats)
                    file_list = ""
                    for file in selected_files:
                        file_list += f'"{file}" '
                    print(file_list)
                    flags = []
                    if values["-o-noexport-"]: 
                        flags.append("--noexport")
                    if values["-o-noprocess-"]:
                        flags.append("--noprocess")
                    if values["-OUT-DIR-"]:
                        dest = f"--dest {values['-OUT-DIR-']}"
                    else:
                        dest = ""
                    command = sg.execute_command_subprocess("python", "t9a_generate_labs.py", file_list, "--quality", ' '.join(qualities), "--formats", ' '.join(formats), ' '.join(flags), dest,pipe_output=True)
                    print(sg.execute_get_results(command)[0])
 
        window.close()
                


    def load_file(filename):
        try:
            lab = LABfile(filename)
            window["-FILE-"].update(filename)
            window["-OPEN-SCRIBUS-"].update(disabled=False)
            window["-OPEN-OLD-RULES-"].update(disabled=False)
            window["-RULES-"].update("...")
            rules_pdf = lab.get_embedded_rules()
            window["-RULES-"].update(rules_pdf)
            window["-OLD-VERSION-"].update(get_version_from_PDF(rules_pdf))
        except ParseError as e:
            window["-FILE-"].update("Not a valid .sla file")
            disable_load()
            return
        except Exception as e:
            print(e)
            window["-RULES-"].update("Error")
        return lab


    def disable_load():
        window["-OPEN-SCRIBUS-"].update(disabled=True)
        window["-OPEN-OLD-RULES-"].update(disabled=True)
        window["-RULES-"].update("")
        window["-OLD-VERSION-"].update("")

    while True:
        event, values = window.read()
        # TODO: change to match->case switch statement
        if event in ["Exit", sg.WIN_CLOSED]:
            break

        if event == "-FILE-":
            filename = values["-FILE-"]
            lab = load_file(filename)
        elif event == "-FILE-LIST-":
            if values[event]:
                data_selected = [lab_list[row] for row in values[event]]
                # filename = values['-FILE-LIST-'][0][1]
                if filename := data_selected[0][1]:
                    if Path(filename).is_file():
                        # window["-FILE-"].update(filename)
                        lab = load_file(filename)
                    else:
                        window["-FILE-"].update("No valid file selected")
                        disable_load()

        elif event == "-NEW-RULES-":
            new_pdf = values["-NEW-RULES-"]
            window['-NEW-RULES-'].update(new_pdf)
            try:
                new_rules_version = get_version_from_PDF(new_pdf)
            except:
                new_rules_version = "ERROR"
            window["-NEW-VERSION-"].update(new_rules_version)
            window["-COMPARE-"].update(disabled=False)
            window["-REPLACE-"].update(disabled=False)
            window["-OPEN-NEW-RULES-"].update(disabled=False)

        elif event == "-COMPARE-":
            rules_pdf = window["-RULES-"].get()
            if not filename or not new_pdf:
                window['-RESULT-'].update("No file selected")
                continue
            window['-RESULT-'].update("Matching...")

            try:
                # TODO: parrallise
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
        elif event == "-REPLACE-":
            nopoints = os.path.splitext(new_pdf)[0] + '_nopoints.pdf'
            new_pdf = copy_file(new_pdf,os.path.dirname(filename)+'/images')
            print(f"checking for nopoints version: {nopoints}")
            if os.path.isfile(nopoints):
                copy_file(nopoints,os.path.dirname(filename)+'/images')
            lab.replace_pdf(new_pdf)
            # replace_rules(filename, new_pdf)
            rules_pdf = lab.get_embedded_rules()
            window["-RULES-"].update(rules_pdf)
            new_version = window["-NEW-VERSION-"].get()
            lab.set_version(new_version)
        elif event == "-OPEN-OLD-RULES-":
            subprocess.Popen(window['-RULES-'].get(), shell=True)
        elif event == "-OPEN-NEW-RULES-":
            subprocess.Popen(new_pdf, shell=True)
        elif event == "-ADD-NEW-":
            # filename = sg.popup_get_file(
            #     'Select a .sla file',  title="File selector", file_types=(("SLA Files", "*.sla"),))
            # new_file = add_file()
            if new_file := add_edit_file():
                lab_list.append(new_file)
                window['-FILE-LIST-'].update(lab_list)
                update_settings_list(settings,lab_list)
        elif event == "-EDIT-SELECTED-":
            selected_row = values["-FILE-LIST-"][0]
            data_selected = lab_list[selected_row]

            new_file = add_edit_file(data_selected)
            lab_list[selected_row] = new_file
            window['-FILE-LIST-'].update(lab_list)
            update_settings_list(settings,lab_list)
        elif event == "-DELETE-SELECTED-":
            selected_row = values["-FILE-LIST-"][0]
            lab_list.pop(selected_row)
            window['-FILE-LIST-'].update(lab_list)
            update_settings_list(settings,lab_list)
        elif event == "-OPEN-SCRIBUS-":
            filename = values["-FILE-"]
            print(f"opening {filename} in Scribus")
            open_scribus(filename)
        elif event == "-EXPORT-MENU-":
            export_menu()
    
    window.close()

main()