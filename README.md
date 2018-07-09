# Table of Contents
- [crp.py](#crppy)
    - [about](#about)
    - [dependencies](#dependencies)
    - [installation](#installation)
        - [python](#python)
        - [installing pip](#installing-pip)
        - [installing ExifTool](#installing-exiftool)
        - [installing the crp_dc script](#installing-the-crp_dc-script)
    - [upgrading](#upgrading)
    - [usage](#usage)

crp_dc
========
Transforms legacy CSV metadata into Dublin Core XML, and extracting technical metadata of digitised files supplied by vendors for the California Revealed Project.

## crp.py

### about

`crp.py` transforms a very specifically formatted CSV file into Dublin Core XML, while also extracting technical metadata of digitised files supplied by vendors for the California Revealed Project.

---
### dependencies
`crp.py` requires:
- `exiftool`
- `lxml`
- `python`
- `pip`
---
### installation

#### python

`python` is installed by default on OSX. You can verify that it is installed by typing:

`python`

in the terminal. You should see something like:
```
$ python
Python 2.7.12 (default, Dec  4 2017, 14:50:18) 
[GCC 5.4.0 20160609] on darwin
Type "help", "copyright", "credits" or "license" for more information.
```

if `python` is installed. If `python` is not installed, then the easiest method of doing so is with `homebrew`.
In order to install `homebrew`, follow the instructions at https://brew.sh/

and when `homebrew` has installed, type:
`brew install python`
in order to install `python`.

---
#### installing pip

The easiest way to install the script is via the python package manager `pip`.

In order to install `pip` on OSX, enter `sudo easy_install pip` in the terminal.

---
#### installing ExifTool

You may have to install `exiftool` as this is used to extract technical metadata.

If using homebrew this can be installed with:

`brew install exiftool`

---
#### installing the crp_dc script
Finally, you can install the script by entering

`pip install crp_dc`

This will also install the `lxml` python XML processing library.

---
### upgrading
To upgrade the script, enter:
`pip install crp_dc -U`

---
### usage
The script takes two arguments:

`-csv` - [OPTIONAL] the full path to the CSV containing descriptive metadata.

`-i` - the full path to the folder containing the folders of digitised files.

However, if the CSV file is located in the same folder as your input folder (as declared with `-i`), then the script will use that CSV and the `-csv` option is not required.

An example command, that assumes that the folder (called `LTO_SHIPMENT`) that you'd like to process is on a drive called `CAVPP-05`, and your CSV file is located in `Downloads` and it is called `millstreet_2018.csv`:

`crp.py -i /Volumes/CAVPP-05/LTO_SHIPMENT -csv /Users/kieran/Downloads/millstreet_2018.csv`

If the CSV file is located in '/Volumes/CAVPP-05/LTO_SHIPMENT', then the command would just be:

`crp.py -i /Volumes/CAVPP-05/LTO_SHIPMENT`
