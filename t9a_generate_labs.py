import os
from pathlib import Path
import subprocess
import argparse
import time
from datetime import datetime
import shutil
import sys
from parse_toc import parse_file
from t9a_add_bookmarks import add_bookmarks
import re
from t9a_sla import LABfile

### Constants ####
HIGH_DPI = 300
LOW_DPI = 100

QUALITY_TYPES = ["high","low","print"]
FORMAT_TYPES = ["full","nopoints","norules"]
##################


def dir_path(path):
    if os.path.isdir(path):
        return path
    else:
        raise argparse.ArgumentTypeError(f"readable_dir:{path} is not a valid path")

def run_command(cmd,text=None,details=False):

    # TODO: create version to log internal functions as well as external
    # TODO: catch errors (return codes?)

    # if not details:
    #     details = args.details
    now = datetime.now()
    time = now.strftime("%H:%M:%S")
    status = f"{time}: "
    if text:
        status += f"{text}"
        if details:
            status += f" -- {cmd}"
    else:
        status += f" Running: {cmd}"
    # print(f"{time}: Running: {cmd}")
    print(status)
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return result

def generate_pdfs(input): # call Scribus to generate PDFs
    format_args = ' '.join(args.formats)
    quality_args = ' '.join(args.quality)
    try:
        run_command(f'scribus "{input}" --no-gui --no-splash -py ./t9a_export_pdfs.py --quit --format {format_args} --quality {quality_args}',
                    text=f"Opening {os.path.basename(input)} in Scribus and exporting PDF(s)")
    except OSError as err:
        print("Couldn't launch Scribus. Make sure that the scribus executable is in your PATH environment variable")
        sys.exit(1)

def rename_file(filename, version):
    t9a_pattern = r't9a-fb_lab_(\w+)_(\w+)_v\d+_(\w+)_(\w+)\.pdf'
    t9a_re = re.compile(t9a_pattern)
    f = os.path.basename(filename).lower()
    version = version.replace(" ","_")
    if result := t9a_re.match(f):
        army = result.group(1)
        lang = result.group(2)
        format = result.group(3)
        quality = result.group(4)
        if quality =="print":
            quality = "press"
        if quality == "low":
            quality = "online"
        if quality == "high":
            quality = "print"
        if format == "norules":
            format = "background"
            new_filename = f"t9a-fb_lab_{quality}_{army}_{format}_{lang}.pdf" # no version string needed for background book
        else:
            new_filename = f"t9a-fb_lab_{quality}_{army}_{format}_{version}_{lang}.pdf"
        return f'{os.path.split(filename)[0]}/' + new_filename.replace("_wdg_", "_wotdg_")
    else:
        print(f"Invalid file name: {f}")

def process_pdf(input): # parse TOC and create bookmarks

    sla = LABfile(input)
    version = sla.get_text("version_number")

    files = []
    if "high" or "low" in args.quality:
        if "full" or "nopoints" in args.formats:
            full_bookmarks = parse_file(input,rules=True)
        if "norules" in args.formats:
            input_norules = str(Path(input).parents[0] / Path(input).stem) + "_norules.sla"
            print(f"parsing: {input_norules}")
            norules_bookmarks = parse_file(input_norules, rules=False)

        for q in args.quality:
            for f in args.formats:
                original_pdf = f"{os.path.splitext(input)[0]}_{f}_{q}.pdf"
                new_pdf = rename_file(original_pdf,version)
                shutil.copy(original_pdf,new_pdf)
                files.append(new_pdf)
                if f in ["full","nopoints"]:
                    add_bookmarks(new_pdf,full_bookmarks)
                else:
                    add_bookmarks(new_pdf,norules_bookmarks)
    if "print" in args.quality:
        # no need for bookmarks in print version
        pass

    # rename and move files
    # files = []
    # for f in args.formats:
    #     for q in args.quality:
    #         new_filename = os.path.splitext(input)[0]+f'_{f}_{q}.pdf'
    #         files.append(new_filename)
    # file_list = '"{0}"'.format('" "'.join(files))
    # result = run_command(f"python ./rename_files.py --keep {file_list}",False,"Renaming files")
    # # print(result)
    return files

def move_pdfs(files, output_dir):
    for f in files:
        shutil.move(f,f"{output_dir}/{os.path.basename(f)}")

def create_nopoints(input):
    cmd = f'python ./replace_pdf.py "{input}" -o' # create a '_nopoints.sla' file
    run_command(cmd,False,"Creating nopoints version of file")


def main(argv):
    global args
    parser = argparse.ArgumentParser()
    # parser.add_argument("input", help=".sla files")
    parser.add_argument('file', type=argparse.FileType('r'), nargs='+')
    parser.add_argument('--noexport', help='Do not export PDFs from Scribus first, use existing files.', action="store_true", default=False)
    parser.add_argument('--noprocess', help='Do not process PDFs after exporting', action="store_true", default=False)
    parser.add_argument('--formats', '-f', nargs='+', help='Options: "full", "nopoints", and "norules". Default is "full".', default=["full", "nopoints"])
    parser.add_argument('--quality', '-q', nargs='+', help='Which qualities of file do you want? Available: "high", "low", and "print". Defaults to "high" and "low"', default=["high", "low"])
    parser.add_argument('--dest','-d', help='destination directory',type=dir_path)
    parser.add_argument('--details', action="store_true", default=False)
    parser.add_argument('--year', '-y')
    parser.add_argument('--version', '-v')
    args = parser.parse_args(argv)

    # TODO: Validate format and quality options (using type= and functions) 

    # print(args.formats)
    # print(args.quality)

    for f in args.file:
        job = f.name
        if not args.noexport:
            print("Trying to run scribus")
            generate_pdfs(job) # TODO: maybe parallelise
        if not args.noprocess:
            new_files = process_pdf(job)
            if args.dest:
                now = datetime.now()
                time = now.strftime("%H:%M:%S")
                print(f"{time}: Moving files to {args.dest}")
                move_pdfs(new_files,args.dest)

    # All done
    now = datetime.now()
    time = now.strftime("%H:%M:%S")
    print(f"{time}: Completed")


if __name__ == '__main__':
    main(sys.argv[1:])

