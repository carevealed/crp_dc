#!/usr/bin/env python
'''
Requires EXIFTOOL
'''
import argparse
import csv
import os
import json
import subprocess
import lxml.etree as ET

def get_exiftool_json(source):
    '''
    Returns JSON object of exiftool output
    '''
    print source
    exiftool_json = subprocess.check_output([
        'exiftool',
        '-J',
        source
    ])
    parsed = json.loads(exiftool_json)
    print json.dumps(parsed, indent=4, sort_keys=True)
    return parsed[0]


def make_dc_object():
    '''
    Generates a minimal lxml Dublin Core object.
    '''
    header = "<metadata xmlns:xsi='http://www.w3.org/2001/XMLSchema-instance' xmlns:dc='http://purl.org/dc/elements/1.1/' xmlns:dcterms='http://purl.org/dc/terms/'></metadata>"
    metadata_parent_element = ET.fromstring(header)
    dublin_core_object = ET.ElementTree(ET.fromstring(header))
    return dublin_core_object

def add_dc_elements(root_metadata_element, dc_namespace):
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
def extract_metadata(csv_file):
    '''
    Read the csv and store the data in a list of dictionaries.
    '''
    object_dictionaries = []
    input_file = csv.DictReader(open(csv_file))
    for rows in input_file:
        object_dictionaries.append(rows)
    return object_dictionaries


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
        help='full path of input directory'
    )
    parser.add_argument(
        '-csv',
        help='Full path to Islandora metadata CSV.'
    )
    parsed_args = parser.parse_args()
    return parsed_args
def add_asset_elements(root_metadata_element):
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
    '''
    Should stop here as all the above will be in every description,
    regardless of complexity. What follows will need relationship
    metadata and counters, regardless of complexity.
    So you just need to create a new 'create_instantiation' function
    that takes the Assetpart element as parent.
    '''
def create_instantiations(AssetPart_element, instantation_counter, status):
    '''
    Create instantiations and build relationships.
    '''
    instantiation_element_list = []
    instantiations_element = create_assets_element(
        index=99,
        parent=AssetPart_element,
        dc_element='instantations'
    )
    instantiation_element = create_assets_element(
        index=99,
        parent=instantiations_element,
        dc_element='instantation'
    )
    technical_element = create_assets_element(
        index=99,
        parent=instantiation_element,
        dc_element='technical'
    )
    counter = 1
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

def analyse_folder(folder_name):
    '''
    Analyze a folder to figure out how complex he package is. Create dictionary
    that lists checksum path, access copy, preservation copy.
    '''
    print 'hi'
    file_info_list = []
    print file_info_list
    contents = sorted(os.listdir(folder_name))
    print contents
    for files in contents:
        if files.endswith('prsv.tif'):
            dictionary = {}
            dictionary['master'] = files
            dictionary['access'] = files.replace('prsv.tif', 'access.jpg')
            dictionary['access_checksum'] = dictionary['access'] + '.md5'
            dictionary['master_checksum'] = dictionary['master'] + '.md5'
            file_info_list.append(dictionary)
    print file_info_list
    return file_info_list
        
def main():
    args = parse_args()
    
    dc_namespace = 'http://purl.org/dc/elements/1.1/'
    dc_terms_namespace = 'http://purl.org/dc/terms/'
    xsi_namespace = 'http://www.w3.org/2001/XMLSchema-instance'
    md = extract_metadata(args.csv)
    source_folder = args.i
    folder_contents = os.listdir(source_folder)
    for folder in folder_contents:
        full_folder_path = os.path.join(source_folder, folder)
        if os.path.isdir(full_folder_path):
            for csv_record in md:
                if csv_record['Object Identifier'] == folder:
                    print('Found %s, processing...') % folder
                    package_info = analyse_folder(full_folder_path)
                    dublin_core_object = make_dc_object()
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
                        dc_language
                    ) = add_dc_elements(root_metadata_element, dc_namespace)
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
                    dc_type.text = csv_record['Format']
                    callNumber.text = csv_record['Call Number']
                    projectIdentifier.text = csv_record['Project Identifier']
                    objectIdentifier.text = csv_record['Object Identifier']
                    assetType.text = csv_record['Asset Type']
                    description.text = csv_record['Description or Content Summary']
                    vendorQualityControlNotes.text = csv_record['Quality Control Notes']
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
                    extent_dimensions.text = csv_record['Extent (dimensions)']
                    # why is there an equals character and quotes in the CSV?
                    created.text = csv_record['Date Created']
                       
                    (   objectIdentifier,
                        callNumber,
                        projectIdentifier,
                        assetType,
                        description,
                        vendorQualityControlNotes
                    ), AssetPart_element = add_asset_elements(root_metadata_element)
                    instantiation_counter = 1
                    for package in package_info:
                    
                        (   digitalFileIdentifier,
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
                        ) = create_instantiations(AssetPart_element, instantiation_counter, status)
                       
                        md5.text = ''
                        exiftool_json = get_exiftool_json(full_folder_path)
                        standardAndFileWrapper.text = exiftool_json['MIMEType']
                        fileExtension.text = exiftool_json["FileTypeExtension"]
                        # Strings needed as INTs returned for some reason..
                        bitDepth.text = str(exiftool_json['BitsPerSample'])
                        imageWidth.text = str(exiftool_json["ImageWidth"])
                        imageLength.text = str(exiftool_json["ImageHeight"])
                        #compression.text = str(exiftool_json["Compression"])
                        xResolution.text = str(exiftool_json["XResolution"])
                        yResolution.text = str(exiftool_json["YResolution"])
                        #samplesPerPixel.text = str(exiftool_json["ColorComponents"])
                    
                    with open(csv_record['Object Identifier'] + 'dc_metadata.xml', 'w') as outFile:
                        dublin_core_object.write(outFile, xml_declaration = True, encoding='UTF-8', pretty_print=True)
    print 'Transformed XML files have been saved in %s' % os.getcwd()

if __name__ == '__main__':
    main()
