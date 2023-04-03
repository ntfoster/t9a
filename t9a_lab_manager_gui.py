from json import load
import subprocess
import PySimpleGUI as sg
import asyncio
from t9a_sla import LABfile
from t9a_pdf import match_titles, get_version_from_PDF
import json

import os.path
from pathlib import Path
import shutil
import subprocess

async def compare_rules(pdf1, pdf2):
    return await asyncio.run(match_titles(pdf1, pdf2))

SETTINGS_FILE = 't9a_lab_manager_settings.json'
CURRENT_LABS = ["ID", "WDG", "DL", "UD", "SE"]

from t9a_base64 import t9a_icon_base64 as T9A_ICON

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

    sg.ChangeLookAndFeel('DarkBlue14')
    settings = get_settings()
    lab_list = [[lab['name'],lab['filename']] for lab in settings['labs']]

    file_list_column = [
        [
            sg.Table(lab_list, enable_events=True, expand_x=True, expand_y=True, key="-FILE-LIST-",headings=["Army","Filename"], auto_size_columns=False,
                            col_widths=[5,40], justification="left", select_mode=sg.TABLE_SELECT_MODE_BROWSE)
        ],
        [
            sg.Button("Add New", key="-ADD-NEW-"),
            sg.Button("Edit selected",key="-EDIT-SELECTED-"),
            sg.Button("Delete selected", key="-DELETE-SELECTED-"),
            sg.Button("Open in Scribus",key="-OPEN-SCRIBUS-",disabled=True),
        ]
    ]

    tools_column = [
        # [sg.Text("Embedded Rules PDF:")],
        [
            sg.Frame("Embedded Rules", [
                [
                    sg.Text("Filename:", size=10,),
                    sg.Text(size=(40, 1), key="-RULES-", expand_x=True,
                            relief=sg.RELIEF_GROOVE, border_width=1)
                ],
                [
                    sg.Text("Version:", size=10,),
                    sg.Text(size=15, key="-OLD-VERSION-",
                            relief=sg.RELIEF_GROOVE, border_width=1),
                    sg.Button("Open PDF", key="-OPEN-OLD-RULES-", disabled=True)
                ],
            ])
        ],
        # [sg.HorizontalSeparator()],
        [
            sg.Frame("New Rules", [
                [
                    sg.Text("Select:",size=10),
                    sg.FileBrowse(key='-NEW-PDF-', enable_events=True),
                ],
                [
                    # sg.In(size=(60,1), enable_events=True, key="-NEW-PDF-",expand_x=True, readonly=True),
                    sg.Text("Filename:", size=10,),
                    sg.Text(size=40, key='-NEW-RULES-',
                            relief=sg.RELIEF_GROOVE, border_width=1),
                ],
                [
                    sg.Text("Version:", size=10),
                    sg.Text(size=15, key='-NEW-VERSION-',
                            relief=sg.RELIEF_GROOVE, border_width=1),
                    sg.Button("Open PDF", key="-OPEN-NEW-RULES-", disabled=True),
                ],
            ])
        ],
        # [sg.HorizontalSeparator()],
        [
            sg.Button("Compare", key="-COMPARE-", disabled=True),
            sg.Text("Result:"),
            sg.Text(size=10, key="-RESULT-", relief=sg.RELIEF_GROOVE,
                    border_width=1, expand_x=True),
            sg.Button("Replace", key="-REPLACE-",
                      disabled=True, button_color="red",),
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


    def add_file():
        add_edit_layout = [
            [
                sg.Text("Army",size=10),
                sg.In(size=(20, 1), key="-NEW-NAME-"),
            ],
            [
                sg.Text("Filename",size=10),
                sg.In(size=(40, 1), key="-NEW-FILE-"),
                sg.FileBrowse(file_types=(("SLA Files", "*.sla"),))
            ],
            [
                sg.Button('OK', key="-SUBMIT-"),
            ]
        ]
        window = sg.Window(
            "Add New File", add_edit_layout, use_default_focus=False, finalize=True, modal=True)
        event, values = window.read()
        if values:
            result = [values['-NEW-NAME-'], values['-NEW-FILE-']]
            window.close()
            return result

    def edit_file(entry):
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
            [
                sg.Button('OK', key="-SUBMIT-"),
            ]
        ]
        window = sg.Window(
            "Edit File", add_edit_layout, use_default_focus=False, finalize=True, modal=True)
        window['-NEW-NAME-'].update(entry[0])
        window['-NEW-FILE-'].update(entry[1])
        event, values = window.read()
        if values:
            result = [values['-NEW-NAME-'],values['-NEW-FILE-']]
            window.close()
            return result

    def load_file(filename):
        lab = LABfile(filename)
        try:
            window["-OPEN-SCRIBUS-"].update(disabled=False)
            window["-OPEN-OLD-RULES-"].update(disabled=False)
            window["-RULES-"].update("...")
            rules_pdf = lab.get_embedded_rules()
            window["-RULES-"].update(rules_pdf)
            window["-OLD-VERSION-"].update(get_version_from_PDF(rules_pdf))
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
                        window["-FILE-"].update(filename)
                        lab = load_file(filename)
                    else:
                        disable_load()

        elif event == "-NEW-PDF-":
            new_pdf = values["-NEW-PDF-"]
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
            print(new_version)
            lab.set_version(new_version)
        elif event == "-OPEN-OLD-RULES-":
            subprocess.Popen(window['-RULES-'].get(), shell=True)
        elif event == "-OPEN-NEW-RULES-":
            subprocess.Popen(new_pdf, shell=True)
        elif event == "-ADD-NEW-":
            # filename = sg.popup_get_file(
            #     'Select a .sla file',  title="File selector", file_types=(("SLA Files", "*.sla"),))
            new_file = add_file()
            lab_list.append(new_file)
            window['-FILE-LIST-'].update(lab_list)
            update_settings_list(settings,lab_list)
        elif event == "-EDIT-SELECTED-":
            selected_row = values["-FILE-LIST-"][0]
            data_selected = lab_list[selected_row]

            new_file = edit_file(data_selected)
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
            # elif event == "-FILE-LIST-": # a file was chosen from the listbox
            #     try:
            #         filename = os.path.join(
            #             values["-FOLDER-"], values["-FILE-LIST-"][0]
            #         )
            #         window["-RULES-"].update(filename)
            #         window["-IMAGE-"].update(filename=filename)
            #     except:
            #         pass
    window.close()

main()