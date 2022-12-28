# crp_dc script version 2
## Table of Contents
- [Overview](#overview)
- [Installation](#installation)
- [Updates](#updates)
- [Software requirements](#software-requirements)
- [Files and filename requirements](#files-and-filename-requirements)
- [Directory structure requirements](#directory-structure-requirements)
- [Spreadsheet requirements](#spreadsheet-requirements)
- [How it all works](#how-it-all-works)
- [Usage for crp2.py (command-line arguments)](#usage-for-crp2.py-(command-line-arguments))
- [Usage for metadata_processor.py (question and answer)](#usage-for-metadata_processor.py-(question-and-answer))
- [Steps for running the script](#steps-for-running-the-scripts)

## Overview
This script will read the input spreadsheet and for each line in the spreadsheet it will read the corresponding column 
cells and map them to metadata fields. It will then build a xml file based on that mapping into a specific sorted order
and then crawl the folder designated by the cell in column `obj_object_identifier` for files to characterize. A xml substructure is attached to the constructed metadata with
core information for each file. 

Image files are handled as follows:
* Anything **not** a PDF with _prsv at the end of the filename is presumed to be a 
Preservation master. 
* Anything **not** a PDF with _access at the end of the filename is presumed to be an Access file.
* Any Access files should have a 1:1 pairing with a Preservation master. If this is not the case an error message will be generated.
* An Access file without a corresponding Preservation
file(s) will be ignored. This matching pair is coupled together in the metadata in a sorted sequence with the lowest number 
marked as Page 1. 
* As _prsv image files may be directly compiled into a PDF, the pairing requirement is not applied to Preservation images.

Born-Digital text files are handled as follows:
* If there is only one PDF it is labelled as an 'object', otherwise PDFs are labelled sequentially as 'File1', 'File2', etc. sequentially in alphabetical order.
* PDFs can be standalone or paired. A PDF ending in _access is labelled as Access and a PDF ending in _prsv is labelled as Preservation.
* Access PDFs will have a derivedFrom metadata tag reflecting all the types of Preservation files within the folder.
* Where only PDF files exist in a folder, there should be a _prsv and an _access PDF file.

## Installation
There are two methods for installation:
1. Follow the steps in order for [Software requirements](#Software-requirements), then
   * Download the entire package from GitHub and extract the ZIP file downloaded. 
2. Use the setup file (easy method):
   * Follow the directions under [Software requirements](#Software-requirements) for installing python3 and exiftool
   * Download the entire package from GitHub and extract the ZIP file downloaded
   * While in the folder with the extracted files, open a terminal window and type `python3 install .`. This should install the software and all dependencies.
   * If the above does not work, you can also try opening a terminal window and running the setup script with `python3 setup.py install`. 
## Updates
Updates differ between installation methods
1. If you followed installation option 1:
   * Download the script you wish to update from GitHub
2. If you followed installation option 2:
   * Follow the directions for option 2 installation again
## Software requirements
### python3
This script requires python3 and was tested for version 3.9. Earlier versions to 3.6 should work but cannot be 
guaranteed. If you are not sure that it is installed, you can check that python is installed on your machine by opening
a terminal or powershell window and typing 'python3'. You should see a message with the python version number and a >>.
Type `exit()` to exit the python window. 
### exiftool (version 12.50 or higher)
This is the core tool used to characterize the files. You can download the latest version from `https://exiftool.org/`. 
Download the version matching your type of system and go through the installation instructions. If using Mac, it is 
important that exiftool is registered in your system paths. This is a tricky thing to do

If using Windows, download the zip file, unzip it and rename the unzipped file called `exiftool(-k).exe` to
`exiftool.exe`. You will need to copy it to the "system path". On a PC this will be `C:\Windows`. Ask your system admin
for how to do this on a server. 

If using Mac, download the zip file, make sure the downloaded file ends in `.dmg`. Double-click on the .dmg file to 
begin installation. It is possible that you will see an "unidentified developer" error message during installation like
so: `"ExifTool-12.52.pkg" can't be opened because it is from an unidentified developer.` If this is the case hold down 
the `ctrl` key, click on the item and selection "Open" from the menu options. You may also circumvent this error by 
lowering the security settings for software installation.  Go to `https://support.apple.com/en-us/HT202491` for details
on how to do this.

After installation on MacOS, check it by opening a terminal window and typing exiftool. If this fails, open the file at 
`~./profile` in a text editor and add the line `export PATH=$PATH:/usr/local/bin`. Save and close.

For the best instructions on doing this with a MacOS system, go to `https://exiftool.org/install.html`.

### pandas (version 1.5.1 or higher)
This is a `python` "library" used to process spreadsheets for the script. In your terminal/powershell type `pip install
pandas`. Alternatively you can try `pip3 install pandas`. This is a complex program so it will take a while.

### openpyxl (version 3.0.10 or higher)
This is a `python` "library" that facilitates processing excel spreadsheets. Once added to python it will work without 
being actively called by a program *but* if not install there is a 50/50 chance a spreadsheet in excel will work in 
pandas. Install with `pip install openpyxl` or `pip3 install openpyxl`

### pyexiftool (version 0.5.4 or higher)
In the script this is called exiftool but the actual "library" is pyexiftool. It facilitates using exiftool, the 
program used to characterize the files, in a "pythonic" way. It gives much more data options compared to the prior 
method of gathering data using exiftool directly. Install with `pip install pyexiftool` or `pip3 install pyexiftool`

## Files and filename requirements

Each file package for characterization must contain files that conform to the file naming convention in the California Revealed Print Statement of work (https://repository.californiarevealed.org/partners/sow).  

File names are based on the Object Identifier (e.g., casmim_000003), which includes the partner’s Marc organization code followed by a unique, sequential number. The Object Identifier (obj_object_identifier) serves as the prefix for all file instantiations associated with the digital object. 

Each package will at minimum contain one of each:
* [`obj_object_identifier`]_prsv.[`extension`] (preservation master file – any text or still image file type)
* [`obj_object_identifier`]_prsv.[`extension`].md5
* [`obj_object_identifier`]_access.[`extension, .pdf or .jpg depending on Media Type`]
* [`obj_object_identifier`]_access.[`extension`].md5

If there are multiple _prsv or _access files there will be an page (_p00X) or file (_f0000X) indicator infix between the object ID and the file generation label to designate the files’ position within the intellectual object. Examples included in the common configurations below. 

Common file configurations are listed below:

* File directory for a single image, Still Image object:
  * casmim_000003_prsv.tif
  * casmim_000003_prsv.tif.md5
  * casmim_000003_access.jpg
  * casmim_000003_access.jpg.md5
* File directory for a single page, Text object:
  * csfpal_000155_prsv.tif
  * csfpal_000155_prsv.tif.md5
  * csfpal_000155_access.pdf
  * csfpal_000155_access.pdf.md5
* File directory for a single source pdf, Text object:
  * casmim_000003_prsv.pdf
  * casmim_000003_prsv.pdf.md5
  * casmim_000003_access.pdf
  * casmim_000003_access.pdf.md5
* File directory for a Still Image object with multiple images, option 1:
  * cwh_000003_p0001_prsv.tif
  * cwh_000003_p0001_prsv.tif.md5
  * cwh_000003_p0002_prsv.tif
  * cwh_000003_p0002_prsv.tif.md5
  * cwh_000003_access.pdf
  * cwh_000003_access.pdf.md5
* cwh_000003_File directory for a Still Image object with multiple images, option 2:
  * cwh_000003_p0001_prsv.tif
  * cwh_000003_p0001_prsv.tif.md5
  * cwh_000003_p0002_prsv.tif
  * cwh_000003_p0002_prsv.tif.md5
  * cwh_000003_p0001_access.jpg
  * cwh_000003_p0001_access.jpg.md5
  * cwh_000003_p0002_access.jpg
  * cwh_000003_p0002_access.jpg.md5
* File directory for a Text object with multiple pages:
  * cwh_000003_p0001_prsv.tif
  * cwh_000003_p0001_prsv.tif.md5
  * cwh_000003_p0002_prsv.tif
  * cwh_000003_p0002_prsv.tif.md5
  * cwh_000003_access.pdf
  * cwh_000003_access.pdf.md5
* File directory for a Text object with sub-pages:
  * cgl_000002_p0001_prsv.tif
  * cgl_000002_p0001_prsv.tif.md5
  * cgl_000002_p0002_001_prsv.tif
  * cgl_000002_p0002_001_prsv.tif.md5
  * cgl_000002_p0002_002_prsv.tif
  * cgl_000002_p0002_002_prsv.tif.md5
  * cgl_000002_access.pdf
  * cgl_000002_access.pdf.md5
* File directory for a multi-source pdf with a single access pdf, Text object:
  * casmim_000003_f00001_prsv.pdf
  * casmim_000003_f00001_prsv.pdf.md5
  * casmim_000003_f00002_prsv.pdf
  * casmim_000003_f00002_prsv.pdf.md5
  * casmim_000003_access.pdf
  * casmim_000003_access.pdf.md5

## Directory structure requirements

The directory structure must conform to California Revealed’s Print Statement of work (https://repository.californiarevealed.org/partners/sow).

Create a folder for each partner, labeled with partner’s Marc organization code, followed by a subfolder for each object that is labeled by the Object Identifier (e.g. CA-R2082/cwh/cwh_000003). The following items should be within each folder per object:
* preservation file(s)
* preservation file .md5(s)
* access file(s)
* access file .md5(s)

## Spreadsheet requirements

This is designed to work with California Revealed’s Print Sent for Digitization export. A sample of which is available here: https://docs.google.com/spreadsheets/d/1K1uRH5NLtP2Mo5UFTe18IobEJrI2jLdrVHIDg_4XWig/edit?usp=sharing

Please note that all lines of the Spreadsheet must contain a value for the field 'obj_object_identifier' for the script to run, identify folders, and identify files to characterize.

## How it all works
The script goes through a series of steps to output an xml file

1. Read the spreadsheet provided
2. For each row, convert the columns into a dictionary where the column name is the key and the cell value is the value
3. Based on decision of metadata type, use a separate mapping dictionary to associate a xml tag with the column name
4. Re-arrange the newly mapped data into a preferred tag order as given in the `ordered_dict` list
5. For each item in the dictionary create an xml tag and plug in the column value
6. If there is a `;` in the column value, split it into components and create a tag for each component
7. If `dc` metadata type, pair in the correct attributes using the `dc_attrib_dict` dictionary
8. Create the asset substructure
9. Crawl the folder as designated by `obj_object_identifier` column value for files not ending in `md5`
10. Create a list of PDF files, a list of not PDF files ending in _prsv, and a list of not PDF files ending in _access
11. Sort each list
12. For each item in the _prsv list create an xml chunk and run characterization using exiftool on the file. Sequentially assign a page number for each
13. If a matching file is found in the _access list, characterize that and append the data
14. For each item in the PDF list, create a xml chunk and run characterization
15. Save an output xml file

## Usage for crp2.py (command line arguments)
The conventional means for running the script are as follows:
1. Open a terminal/powershell window.
2. Type `python crp2.py -i [folderpath] -d [data spreadsheet] -o [output metadata format]`.
   * `-i [folderpath]` is the path to the folder of files to process. This should have subfolders. Example: 
   `"C:\Users\ca_reveal\CA-R PT DublinCore XML Python Script Project - 2022-11\Example Metadata Exports and Directories\cscrm_DG"`
   * `-d [data spreadsheet]` is the filepath to the spreadsheet with metadata for the subfolders in the folderpath. 
   Example: `"C:\Users\ca_reveal\CA-R PT DublinCore XML Python Script Project - 2022-11\Example Metadata Exports and Directories\cscrm_DG_4Test.csv"`
   * `-o [output metadata format]` is the type of metadata to export. Thus **MUST** be either dcterms or dc. Example: `-o dcterms`.
3. Watch the program run until completion.
4. Check the output logs for details on the export.

## Usage for metadata_processor.py (question and answer)
The conventional means for running the script are as follows:
1. Open a terminal/powershell window.
2. Type `python3 metadata_processor.py`.
3. Answer the question prompts as they appear.
   * `enter the spreadsheet name including filepath:` you can drag the spreadsheet file onto the terminal window or you
   can manually enter the spreadsheet name. It is important that the filepath be included.
   * `enter root filepath:` you can drag the folder to be processed or type in the name including filepath. If you do 
   not include a folder it will fail.
   * `type 'dcterms' for qualified dublin core, type 'dc' for simple dublin core:` You have a choice of simple dublin 
   core or qualified dublin core, type in the abbreviation for that. The tags are **very** different and not 
   interchangeable.
4. Watch the program run until completion.
5. Check the output logs for details on the export.

## Steps for running the scripts
1. Set-up
   * Install python3
   * Install exiftool
   * Download the package from gitHub
   * Run setup file **OR** install python dependencies *in the order* listed
2. Execution
   * **Option 1:** crp2.py (command-line arguments option)
     * Open a terminal window and type `python3 crp2.py`
       * input the command-line arguments as follows:
         * `-i [full path to the folder to process]` where the brackets and contents are replaced by the full folderpath
         * `-d [full path to spreadsheet]` where the brackets and contents are replaced by the full filepath to the spreadsheet with metadata
         * `-o [dc or dcterms]` where the brackets and contents are replaced by either dcterms (new metadata format) or dc (old metadata format)
         * *Example:* ` python crp2.py -i "C:\Users\ca_reveal\CA-R PT DublinCore XML Python Script Project - 2022-11\Example Metadata Exports and Directories\cscrm_DG" -d "C:\Users\ca_reveal\CA-R PT DublinCore XML Python Script Project - 2022-11\Example Metadata Exports and Directories\cscrm_DG_4Test.csv" -o dcterms`
       * **NOTE:** if there are spaces in the filepath/folderpath you *must* put it in quotations
   * **Option 2:** metadata_processor.py (question and answer option)
     * Invoke the script in the terminal window 
       * dragging it onto an option terminal window or
       * typing `python3 metadata_processor.py`
       * typing the command `python3 metadata_processor.py` while in the same folder as the script
       * Answer the questions in the prompt