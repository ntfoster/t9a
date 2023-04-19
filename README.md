This is a collection of scripts to help with creating and updating The Ninth Age Full Army Books in [Scribus](https://www.scribus.net) (1.5.8+).

# Scribus Tools

The main script to use within Scribus is `t9a_scribus_lab_tools_gui.py`. Run this script from the menu bar with Scripts > Execute Script (or Recent Scripts if you've already used it recently).

This script can perform the following functions:
1. **Create Table of Contents** - Scans text frames in the document for uses of the styles `HEADER Level 1`, `HEADER Level 2`, `HEADER Rules` and creates the Table of Contents in frames called `TOC_Background` and `TOC_Rules`, using styles `TOC Level 1`, `TOC Level 2` and `TOC_Rules`
2. **Create ToC Hyperlinks** - Scans the entries in the TOC_Background and TOC_Rules frames, and creates a clickable hyperlink (aka PDF Annotation) on the Hyperlinks layer for each entry set to the corresponding page number. **Note:** currently doesn't handle entries that span more than one line.
3. **Set Footers** - Creates running footer text frame on each page after the contents showing the most recent chapter heading (i.e. text with `HEADER Level 1` style)
4. **Add rules Headers** - Reads headings from a JSON file (if present) associated with the embedded rules PDF, and creates corresponding headers on the Notes layer with the `HEADER Rules` style. Used to create Table of Contents for the rules pages. More info below on generating the JSON file.
5. **Replace rules PDF**  - Lets you pick a new pdf to replace the embedded rules PDF.

## Export

Let's you pick the formats and quality presets to export the Army Book. Files will be created in the same directory as the currently open .sla file.

The LAB Manager program detailed below has options for post-processing these files by adding bookmarks, renaming to fit the T9A scheme, and collecting in an output directory.

# LAB Manager
Run `lab_manager.py` (either from commmand line or double-clicking). Will not work within Scribus (uses Python packges not available in the standard library in Scribus).

This is a GUI application to manage different Full Army Book files, replace PDFs and export final versions.