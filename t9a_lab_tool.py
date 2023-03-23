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

async def compare_rules(pdf1, pdf2):
    return await asyncio.run(match_titles(pdf1, pdf2))

SETTINGS_FILE = 'settings.json'

def copy_file(file,directory):
    destination = directory+'/'+os.path.basename(file)
    print(f"Copying {file} to {destination}")
    try:
        shutil.copy(file,destination)
    except shutil.SameFileError:
        print("Old file and new file are the same")
    return destination


def main():

    with open(SETTINGS_FILE) as json_file:
        settings = json.load(json_file)    
        LABS = settings['labs']

    file_list_column = [
        [
            # sg.Listbox(LABS, size=(60,6), auto_size_text=True, enable_events=True, select_mode="LISTBOX_SELECT_MODE_SINGLE", expand_y=True, key="-FILE-LIST-"),
            sg.Table(LABS, enable_events=True, expand_y=True, key="-FILE-LIST-",headings=["Army","Filename"], auto_size_columns=False,
                            col_widths=[5,50], justification="left", select_mode=sg.TABLE_SELECT_MODE_BROWSE)
        ]
    ]

    tools_column = [
        [sg.Text("Embedded Rules PDF:")],
        [sg.Text(size=(60,1),key="-RULES-",expand_x=True)],
        [
            sg.Text("Rules version:"),
            sg.Text(key="-OLD-VERSION-")
        ],
        [
            sg.Button("Open in Scribus",key="-OPEN-SCRIBUS-",disabled=True),
            sg.Button("Open Rules PDF",key="-OPEN-OLD-RULES-",disabled=True)
        ],
        [sg.HorizontalSeparator()],

        [sg.Text("Replace PDF\n---\nChoose new rules PDF")],
        [
            sg.In(size=(20,1), enable_events=True, key="-NEW-PDF-",expand_x=True, readonly=True),
            sg.FileBrowse()
        ],
        [
            sg.Text("Rules version:"),
            sg.InputText('No file selected ', justification='left',text_color='black', background_color='white', key='-NEW-VERSION-')
            # sg.Text(key="-NEW-VERSION-")
        ],
        [
            sg.Button("Replace",key="-REPLACE-",disabled=True,button_color="red"),
            sg.Button("Open Rules PDF",key="-OPEN-NEW-RULES-",disabled=True),
            sg.Button("Compare",key="-COMPARE-",disabled=True),
            sg.Text(key="-RESULT-")
        ],

    ]


    # Full layout
    layout = [
        [
            sg.Text("LAB .sla file"),
            sg.In(size=(60,1), enable_events=True, key="-FILE-",expand_x=True, readonly=True),
            sg.FileBrowse()
        ],

        [
            sg.Col(file_list_column, vertical_alignment="top",expand_y=True),
            sg.Col(tools_column, vertical_alignment="top")
        ]
    ]

    sg.ChangeLookAndFeel('DarkPurple')
    window = sg.Window("T9A LAB Details", layout, resizable=True)
    filename = None
    new_pdf = None

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


    while True:
        event, values = window.read()
        if event in ["Exit", sg.WIN_CLOSED]:
            break

        # Folder name was filled in, make a list of files in the folder
        if event == "-FILE-":
            filename = values["-FILE-"]
            lab = load_file(filename)
        elif event == "-FILE-LIST-":
            data_selected = [LABS[row] for row in values[event]]
            # filename = values['-FILE-LIST-'][0][1]
            filename = data_selected[0][1]
            window["-FILE-"].update(filename)
            lab = load_file(filename)

        elif event == "-NEW-PDF-":
            new_pdf = values["-NEW-PDF-"]
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