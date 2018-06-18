#!/usr/bin/env python
'''
Requires EXIFTOOL
'''
import argparse
import csv
import os
import sys
import json
import subprocess
import lxml.etree as ET


def parse_args():
    '''
    Parse command line arguments.
    '''
    parser = argparse.ArgumentParser(
        description='Harvest metadata and generate Dublin Core XML'
        ' Written by Kieran O\'Leary for the California Revealed Project.'
    )
    parser.add_argument(
        '-i',
        help='full path of input directory', required=True
    )
    parser.add_argument(
        '-csv',
        help='Full path to Islandora metadata CSV.'
    )
    parsed_args = parser.parse_args()
    return parsed_args


def csv_extract(csv_file):
    '''
    Read the csv and store the data in a list of dictionaries.
    '''
    object_dictionaries = []
    input_file = csv.DictReader(open(csv_file, 'rU'))
    for rows in input_file:
        object_dictionaries.append(rows)
    return object_dictionaries


def analyse_folder(folder_name):
    '''
    Analyze a folder to figure out how complex he package is. Create dictionary
    that lists checksum path, access copy, preservation copy.
    '''
    file_info_list = []
    contents = sorted(os.listdir(folder_name))
    for files in contents:
        if files.endswith('prsv.tif'):
            dictionary = {}
            dictionary[
                'Preservation'
            ] = os.path.join(folder_name, files)
            dictionary[
                'Access'
            ] = os.path.join(folder_name, files.replace('prsv.tif', 'access.jpg'))
            dictionary[
                'access_checksum'
            ] = dictionary['Access'] + '.md5'
            dictionary[
                'master_checksum'
            ] = dictionary['Preservation'] + '.md5'
            file_info_list.append(dictionary)
    return file_info_list


def add_DC_metadata(folder, dc_namespace, xsi_namespace, csv_record):
    print('- Found %s, processing...') % folder
    dublin_core_object = make_dc_object()
    # Sets up a bunch of empty Dublin Core XML elements.
    root_metadata_element = dublin_core_object.getroot()
    (
        dc_identifier,
        dc_crp_provenance,
        dc_provenance,
        dc_type,
        dc_format,
        dc_title,
        dc_creator,
        dc_rights,
        dc_rights_country,
        dc_language,
        dc_date
    ) = add_dc_elements(root_metadata_element, dc_namespace)
    # Populate the empty elements with the corresponding CSV field.
    dc_identifier.attrib["{%s}type" % xsi_namespace] = "dcterms:URI"
    dc_rights_country.attrib["type"] = 'Country of Creation'
    dc_rights.text = csv_record['Copyright Statement']
    dc_rights_country.text = csv_record['Country of Creation']
    dc_crp_provenance.text = 'California Revealed Project'
    dc_provenance.text = csv_record['Institution']
    dc_format.text = csv_record['Generation']
    dc_title.text = csv_record['Main or Supplied Title']
    dc_creator.text = csv_record['Creator']
    dc_identifier.text = csv_record['Internet Archive URL']
    dc_type.text = csv_record['Type']
    dc_date.attrib["type"] = 'Issued'
    dc_date.text = csv_record['Date Published']
    dc_language.text = csv_record['Language']
    return root_metadata_element, dublin_core_object


def create_dc_element(index, parent, dc_element, dublin_core_namespace):
    '''
    Adds an empty metadata element to dublin_core_object
    Args:
    index = Order in which element should appear below parent.
    parent = Parent element of the new element.
    dc_element = Name, without namespace of your Dublin Core element.
    dublin_core_namespace = Literally the DC namespace.
    Returns: The element object itself, just incase the script needs to access it.
    '''
    dc_element = ET.Element("{%s}%s" % (dublin_core_namespace, dc_element))
    parent.insert(index, dc_element)
    return dc_element


def add_asset_elements(root_metadata_element):
    '''
    Adds the Asset level elements.
    '''
    asset_element_list = []
    Assets_element = create_assets_element(
        index=99,
        parent=root_metadata_element,
        dc_element='Assets'
    )
    for asset_level_elements in [
            'objectIdentifier',
            'callNumber',
            'projectIdentifier',
            'assetType',
            'description',
            'vendorQualityControlNotes'
    ]:
        am = create_assets_element(
            index=99,
            parent=Assets_element,
            dc_element=asset_level_elements
        )
        asset_element_list.append(am)
    AssetPart_element = create_assets_element(
        index=99,
        parent=Assets_element,
        dc_element='AssetPart'
        )
    return asset_element_list, AssetPart_element


def get_exiftool_json(source):
    '''
    Returns JSON object of exiftool output
    '''
    exiftool_json = subprocess.check_output([
        'exiftool',
        '-J',
        source
    ])
    parsed = json.loads(exiftool_json)
    # print json.dumps(parsed, indent=4, sort_keys=True)
    return parsed[0]


def make_dc_object():
    '''
    Generates a minimal lxml Dublin Core object containing the DC namespace header.
    '''
    header = "<metadata xmlns:xsi='http://www.w3.org/2001/XMLSchema-instance' xmlns:dc='http://purl.org/dc/elements/1.1/' xmlns:dcterms='http://purl.org/dc/terms/'></metadata>"
    dublin_core_object = ET.ElementTree(ET.fromstring(header))
    return dublin_core_object


def add_dc_elements(root_metadata_element, dc_namespace):
    '''
    Adds some of the basic DC elements to the XML object.
    '''
    counter = 1
    element_list = []
    for elements in [
            'identifier',
            'provenance',
            'provenance',
            'type',
            'format',
            'title',
            'creator',
            'rights',
            'rights',
            'language',
            'date'
        ]:
        element = create_dc_element(
            index=counter,
            parent=root_metadata_element,
            dc_element=elements,
            dublin_core_namespace=dc_namespace
        )
        element_list.append(element)
        counter += 1
    return element_list


def extract_checksum(manifest):
    '''
    Extracts the MD5 checksum from a manifest.
    '''
    with open(manifest, 'r') as manifest_object:
        manifest_line = manifest_object.readlines()
    checksum = manifest_line[0][:32]
    return checksum


def create_assets_element(index, parent, dc_element):
    '''
    Adds an empty metadata element to dublin_core_object
    Args:
    index = Order in which element should appear below parent.
    parent = Parent element of the new element.
    dc_element = Name, without namespace of your Dublin Core element.
    dublin_core_namespace = Literally the DC namespace.
    Returns: The element object itself, just incase the script needs to access it.
    '''
    dc_element = ET.Element(dc_element)
    parent.insert(index, dc_element)
    return dc_element


def create_instantiations(AssetPart_element, instantation_counter, generation):
    '''
    Create instantiations and build relationships.
    '''
    counter = 1
    instantiation_element_list = []
    instantiations_element = create_assets_element(
        index=99,
        parent=AssetPart_element,
        dc_element='instantations'
    )
    instantiations_element.attrib["relationship"] = 'Page %s' % str(instantation_counter)
    instantiation_element = create_assets_element(
        index=99,
        parent=instantiations_element,
        dc_element='instantation'
    )
    instantiation_element.attrib["generation"] = generation
    technical_element = create_assets_element(
        index=99,
        parent=instantiation_element,
        dc_element='technical'
    )
    for elements in [
            'digitalFileIdentifier',
            'creationDate',
            'fileExtension',
            'standardAndFileWrapper',
            'size',
            'bitDepth',
            'imageWidth',
            'imageLength',
            'compression',
            'samplesPerPixel',
            'xResolution',
            'yResolution',
            'md5',
            'creatingApplicationAndVersion',
            'derivedFrom',
            'digitizerManufacturer',
            'digitizerModel',
            'imageProducer'
    ]:
        element = create_assets_element(
            index=counter,
            parent=technical_element,
            dc_element=elements,
        )
        instantiation_element_list.append(element)
        counter += 1
    return instantiation_element_list


def techncial_metadata(package_info, AssetPart_element, csv_record):
    '''
    Create technical metadata for instantiations
    '''
    instantiation_counter = 1
    for package in package_info:
        for sub_item in sorted(package.keys(), reverse=True):
            if sub_item == 'Access' or sub_item == 'Preservation':
                (digitalFileIdentifier,
                 creationDate,
                 fileExtension,
                 standardAndFileWrapper,
                 size,
                 bitDepth,
                 imageWidth,
                 imageLength,
                 compression,
                 samplesPerPixel,
                 xResolution,
                 yResolution,
                 md5,
                 creatingApplicationAndVersion,
                 derivedFrom,
                 digitizerManufacturer,
                 digitizerModel,
                 imageProducer
                ) = create_instantiations(AssetPart_element, instantiation_counter, generation=sub_item)
                md5.text = ''
                exiftool_json = get_exiftool_json(package[sub_item])
                digitalFileIdentifier.text = os.path.basename(package[sub_item])
                # This replaces the colons with dashes via the exiftool output.
                creationDate.text = exiftool_json['FileModifyDate'].replace(':', '-', 2)[:19]
                # megabytes rounded to two decimal places.
                size.text = str(round(os.path.getsize(package[sub_item]) / 1024 / 1024.0, 2))
                size.attrib['unit'] = 'megabytes'
                standardAndFileWrapper.text = exiftool_json['MIMEType']
                fileExtension.text = exiftool_json["FileTypeExtension"]
                # Strings needed as INTs returned for some reason..
                if len(str(exiftool_json['BitsPerSample'])) > 1:
                    # Probably best to find some other way of getting
                    # a bits per pixel value rather than this method.
                    bits = str(exiftool_json['BitsPerSample']).split()
                    bits = [int(i) for i in bits]
                    bitDepth.text = str(sum(bits))
                else:
                    bitDepth.text = str(int(exiftool_json['BitsPerSample']) * int(exiftool_json["ColorComponents"]))
                imageWidth.text = str(exiftool_json["ImageWidth"])
                imageLength.text = str(exiftool_json["ImageHeight"])
                xResolution.text = str(exiftool_json["XResolution"])
                yResolution.text = str(exiftool_json["YResolution"])
                if sub_item == 'Preservation':
                    derivedFrom.text = csv_record['Object Identifier']
                    md5.text = extract_checksum(package['master_checksum'])
                elif sub_item == 'Access':
                    derivedFrom.text = os.path.basename(package['Preservation'])
                    md5.text = extract_checksum(package['access_checksum'])
                try:
                    samplesPerPixel.text = str(exiftool_json["ColorComponents"])
                except KeyError:
                    samplesPerPixel.getparent().remove(samplesPerPixel)
                try:
                    compression.text = str(exiftool_json["Compression"])
                except KeyError:
                    compression.getparent().remove(compression)
                try:
                    creatingApplicationAndVersion.text = str(exiftool_json["CreatorTool"])
                except KeyError:
                    creatingApplicationAndVersion.getparent().remove(creatingApplicationAndVersion)
                try:
                    digitizerManufacturer.text = str(exiftool_json["Make"])
                except KeyError:
                    digitizerManufacturer.getparent().remove(digitizerManufacturer)
                try:
                    digitizerModel.text = str(exiftool_json["Model"])
                except KeyError:
                    digitizerModel.getparent().remove(digitizerModel)
        instantiation_counter += 1


def find_csv(source_directory):
    '''
    Attempts to find a CSV file in the source directory.
    This will just use the first CSV that it finds.
    '''
    csv_path = ''
    file_list = os.listdir(source_directory)
    for files in file_list:
        if files.endswith('.csv'):
            if not files.startswith('.'):
                csv_path = os.path.join(source_directory, files)
                continue
    if csv_path == '':
        print('- No CSV found in your source directory. Either declare the location of the CSV file manually or place the CSV in %s') % source_directory
        print('- Exiting')
        sys.exit()
    print('- This CSV file will be used as the metadata source: %s') % csv_path
    return csv_path


def main():
    # Create args object which holds the command line arguments.
    print('\n- California Revealed Project Dublin Core Metadata Generator - v0.6')
    args = parse_args()
    # Declare appropriate XML namespaces.
    dc_namespace = 'http://purl.org/dc/elements/1.1/'
    dc_terms_namespace = 'http://purl.org/dc/terms/'
    xsi_namespace = 'http://www.w3.org/2001/XMLSchema-instance'
    # Check if a CSV is declared with the -csv flag, or if the CSV is present
    # in the source directory.
    if args.csv:
        # check if input is a CSV file
        if not args.csv.endswith('.csv'):
            print('- The file that you provided with the -csv option is not a CSV file')
            print('- Exiting...')
            sys.exit()
        else:
            csv_file = args.csv
    else:
        csv_file = find_csv(args.i)
    # Extracts metadata from the CSV file.
    csv_data = sorted(csv_extract(csv_file))
    source_folder = args.i
    print('- The following folder: %s will be analysed against this CSV file: %s') % (args.i, csv_file)
    folder_contents = os.listdir(source_folder)
    for folder in sorted(folder_contents):
        full_folder_path = os.path.join(source_folder, folder)
        if os.path.isdir(full_folder_path):
            # Loop through all records in the CSV.
            for csv_record in csv_data:
                # Only proceed if the Object Identifier in the CSV record matches
                # the folder name that is currently being analysed.
                package_info = analyse_folder(full_folder_path)
                if csv_record['Object Identifier'] == folder:
                    root_metadata_element, dublin_core_object = add_DC_metadata(
                        folder,
                        dc_namespace,
                        xsi_namespace,
                        csv_record
                    )
                    term_list = []
                    for term in ['medium', 'extent', 'extent', 'created']:
                        dc_term = create_dc_element(
                            index=5,
                            parent=root_metadata_element,
                            dc_element=term,
                            dublin_core_namespace=dc_terms_namespace
                        )
                        term_list.append(dc_term)
                    medium, extent_total, extent_dimensions, created = term_list
                    extent_total.text = csv_record['Total Number of Pages']
                    medium.text = csv_record['Format']
                    extent_dimensions.text = csv_record['Extent (dimensions)']
                    # why is there an equals character and quotes in the CSV?
                    created.text = csv_record['Date Created']
                    (objectIdentifier,
                     callNumber,
                     projectIdentifier,
                     assetType,
                     description,
                     vendorQualityControlNotes
                    ), AssetPart_element = add_asset_elements(root_metadata_element)
                    callNumber.text = csv_record['Call Number']
                    projectIdentifier.text = csv_record['Project Identifier']
                    objectIdentifier.text = csv_record['Object Identifier']
                    assetType.text = csv_record['Asset Type']
                    description.text = csv_record['Description or Content Summary']
                    vendorQualityControlNotes.text = csv_record['Quality Control Notes']
                    techncial_metadata(package_info, AssetPart_element, csv_record)
                    with open(os.path.join(full_folder_path, csv_record['Object Identifier']) + '_metadata.xml', 'w') as outFile:
                        dublin_core_object.write(outFile, xml_declaration=True, encoding='UTF-8', pretty_print=True)
    print('- Finished')


if __name__ == '__main__':
    main()
