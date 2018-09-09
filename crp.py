#!/usr/bin/python
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

def check_for_macroman(csv_record):
    '''
    Some CSV files use macroman encoding instead of utf-8.
    This particularly shows up in the use of spaces.
    This function will check if a field contains these encodings,
    and it will decode them so that they display correctly.
    This may result in incorrect character encodings if non UTF-8
    CSV data is encoded using something other than macroman.
    '''
    for field in csv_record:
        try:
            csv_record[field].decode('utf-8')
        except UnicodeError:
            csv_record[field] = csv_record[field].decode('macroman')
            print(' - Non UTF-8 characters detected, auto-converting using macroman encoding instead')
    return csv_record

def analyse_folder(folder_name):
    '''
    Analyze a folder to figure out how complex he package is. Create dictionary
    that lists checksum path, access copy, preservation copy.
    '''
    file_info_list = []
    contents = sorted(os.listdir(folder_name))
    for files in contents:
        if not files.startswith('.'):
            if not files.endswith('_01_prsv.tif'):
                if files.endswith('prsv.tif'):
                    dictionary = {}
                    dictionary[
                        'Preservation'
                    ] = os.path.join(folder_name, files)
                    if os.path.isfile(os.path.join(folder_name, files.replace('prsv.tif', '01_prsv.tif'))):
                        dictionary[
                            'Preservation_01'
                        ] = os.path.join(folder_name, files.replace('prsv.tif', '01_prsv.tif'))
                        dictionary[
                            'Preservation_01_md5'
                        ] = os.path.join(folder_name, files.replace('prsv.tif', '01_prsv.tif') + '.md5')
                        dictionary[
                            'Access_01'
                        ] = os.path.join(folder_name, files.replace('prsv.tif', '01_access.jpg'))
                        dictionary[
                            'Access_01_md5'
                        ] = os.path.join(folder_name, files.replace('prsv.tif', '01_access.jpg') + '.md5')
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
                elif files.endswith('.pdf'):
                    dictionary = {}
                    dictionary[
                        'Print'
                    ] = os.path.join(folder_name, files)
                    dictionary[
                        'print_checksum'
                    ] = dictionary['Print'] + '.md5'
                    file_info_list.append(dictionary)

    return file_info_list


def add_DC_metadata(folder, dc_namespace, xsi_namespace, csv_record):
    print('- Found %s, processing...') % folder
    dublin_core_object = make_dc_object()
    # Sets up a bunch of empty Dublin Core XML elements.
    root_metadata_element = dublin_core_object.getroot()
    (
        dc_identifier_object_id,
        dc_identifier_call_number,
        dc_identifier_projectID,
        dc_identifier,
        dc_identifier_cdnp,
        dc_crp_provenance,
        dc_provenance,
        dc_provenance_url,
        dc_type,
        dc_format,
        dc_title,
        dc_title_series,
        dc_description_volume,
        dc_description_issue,
        dc_medium,
        dc_extent_total,
        dc_extent_size,
        description,
        dc_creator,
        dc_contributor,
        dc_date,
        dc_rights_country,
        dc_rights,
        dc_rights_holder,
        dc_rights_holderinfo,
        dc_rights_holder_date,
        dc_rights_holder_notice,
        dc_rights_institutional_rights,
        dc_publisher,
        dc_language,
        dc_description_additional_descriptive,
        dc_description_additional_technical,
        dc_relation_collection_guide_title,
        dc_relation_collection_guide_url,
        dc_subject_topic,
        dc_subject_entity,
        dc_coverage,
        dc_coverage_spatial,
        dc_coverage_temporal,
        dc_relation,
        vendorQualityControlNotes
    ) = add_dc_elements(root_metadata_element, dc_namespace)
    # Populate the empty elements with the corresponding CSV field.
    dc_identifier.attrib["{%s}type" % xsi_namespace] = "dcterms:URI"
    dc_rights_country.attrib["type"] = 'Country of Creation'
    dc_rights.text = csv_record['Copyright Statement']
    dc_rights.attrib["type"] = 'copyrightStatement'
    dc_rights_holder.text = csv_record['Copyright Holder']
    dc_rights_holder.attrib["type"] = 'copyrightHolder'
    dc_rights_holderinfo.text = csv_record['Copyright Holder Info']
    dc_rights_holderinfo.attrib["type"] = 'copyrightHolderInfo'
    dc_rights_holder_date.text = csv_record['Copyright Date']
    dc_rights_holder_date.attrib["type"] = 'copyrightDate'
    dc_rights_holder_notice.text = csv_record['Copyright Notice']
    dc_rights_holder_notice.attrib["type"] = 'copyrightNotice'
    dc_rights_institutional_rights.text = csv_record['Institutional Rights Statement (URL)']
    dc_rights_institutional_rights.attrib["type"] = 'copyrightInstitution'
    # this is now in the description section, not rights.
    dc_rights_country.text = csv_record['Country of Creation']
    dc_rights_country.attrib["type"] = 'countryCreated'
    dc_crp_provenance.text = 'California Revealed'
    dc_crp_provenance.attrib["type"] = 'projectNote'
    dc_provenance.text = csv_record['Institution']
    dc_provenance.attrib["type"] = 'institution'
    dc_provenance_url.text = csv_record['Institution URL']
    dc_provenance_url.attrib["type"] = 'institutionURL'
    dc_format.text = csv_record['Generation']
    dc_title.text = csv_record['Main or Supplied Title']
    dc_title.attrib["type"] = 'main'
    dc_creator.text = csv_record['Creator']
    dc_contributor.text = csv_record['Contributor']
    dc_identifier_object_id.attrib["type"] = 'objectIdentifier'
    dc_identifier_call_number.attrib["type"] = 'callNumber'
    dc_identifier_projectID.attrib["type"] = 'projectIdentifier'
    dc_identifier_object_id.text = csv_record['Object Identifier']
    dc_identifier_call_number.text = csv_record['Call Number']
    dc_identifier_projectID.text = csv_record['Project Identifier']
    dc_identifier.text = csv_record['Internet Archive URL']
    dc_identifier.attrib["type"] =  'IAurl'
    dc_type.text = csv_record['Type']
    dc_date.attrib["type"] = 'dcterms:published'
    dc_date.text = csv_record['Date Published']
    dc_publisher.text = csv_record['Publisher']
    dc_language.text = csv_record['Language']
    dc_identifier_cdnp.text = csv_record['CDNP Identifier']
    dc_identifier_cdnp.attrib["type"] = 'CDNPIdentifier'
    dc_description_volume.text = csv_record['Serial Volume']
    dc_description_volume.attrib["type"] = 'serialVolume'
    description.text = csv_record['Description or Content Summary']
    description.attrib["type"] = 'contentSummary'
    vendorQualityControlNotes.text = csv_record['Quality Control Notes']
    vendorQualityControlNotes.attrib["type"] = 'vendorQualityControlNotes'
    dc_title_series.attrib["type"] = 'series'
    dc_title_series.text = csv_record['Series Title']
    dc_description_issue.text = csv_record['Serial Issue']
    dc_description_issue.attrib["type"] = 'serialIssue'
    try:
        dc_extent_total.text = csv_record['Extent (total number of pages)']
    except KeyError:
        try:
            print('- "Extent (total number of pages" value is missing from CSV')
            print('- Using "Total number of pages" instead')
            dc_extent_total.text = csv_record['Total number of pages']
        except KeyError:
            print('- "Total Number of Pages" value is missing from CSV')
            print('- Using "Total Number of Reels or Tapes" instead')
            dc_extent_total.text = csv_record['Total Number of Reels or Tapes']
    dc_medium.text = csv_record['Format']
    dc_extent_size.text = csv_record['Extent (dimensions)']
    dc_extent_total.attrib["type"] = 'dcterms:extent'
    dc_medium.attrib["type"] = 'dcterms:medium'
    dc_extent_size.attrib["type"] = 'dcterms:extent'
    dc_description_additional_descriptive.text = csv_record['Additional Descriptive Notes for Overall Work']
    dc_description_additional_descriptive.attrib["type"] = 'additionalDescriptive'
    dc_description_additional_technical.text = csv_record['Additional Technical Notes for Overall Work']
    dc_description_additional_technical.attrib["type"] = 'additionalTechnical'
    dc_relation_collection_guide_title.text = csv_record['Collection Guide Title']
    dc_relation_collection_guide_title.attrib["type"] = 'isPartof'
    dc_relation_collection_guide_url.text = csv_record['Collection Guide URL']
    dc_relation_collection_guide_url.attrib["type"] = 'isPartof'
    dc_subject_topic.text = csv_record['Subject Topic']
    dc_subject_topic.attrib["type"] = 'topic'
    dc_subject_entity.text = csv_record['Subject Entity']
    dc_subject_entity.attrib["type"] = 'entity'
    dc_coverage.text = csv_record['Publication Location']
    dc_coverage.attrib["type"] = 'publicationLocation'
    dc_coverage_spatial.text = csv_record['Spatial Coverage']
    dc_coverage_spatial.attrib["type"] = 'spatial'
    dc_coverage_temporal.text = csv_record['Temporal Coverage']
    dc_coverage_temporal.attrib["type"] = 'temporal'
    dc_relation.text = csv_record['Relationship']
    dc_relation.attrib["type"] = csv_record['Relationship Type']
    return root_metadata_element, dublin_core_object, dc_contributor, dc_title


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
    dc_namespace = 'http://purl.org/dc/elements/1.1/'
    asset_element_list = []
    Assets_element = create_assets_element(
        index=99,
        parent=root_metadata_element,
        dc_element='Assets'
    )
    for asset_level_elements in [
            'identifier',
            'identifier',
            'identifier',
            'type',
    ]:
        '''
        am = create_assets_element(
            index=99,
            parent=Assets_element,
            dc_element=asset_level_elements
        )
        '''
        am = create_dc_element(
            index=99,
            parent=Assets_element,
            dc_element=asset_level_elements,
            dublin_core_namespace=dc_namespace
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
            'identifier',
            'identifier',
            'identifier',
            'identifier',
            'provenance',
            'provenance',
            'provenance',
            'type',
            'format',
            'title',
            'title',
            'description',
            'description',
            'format',
            'format',
            'format',
            'description',
            'creator',
            'contributor',
            'date',
            'description',
            'rights',
            'rights',
            'rights',
            'rights',
            'rights',
            'rights',
            'publisher',
            'language',
            'description',
            'description',
            'relation',
            'relation',
            'subject',
            'subject',
            'coverage',
            'coverage',
            'coverage',
            'relation',
            'description'
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
        index=999999,
        parent=AssetPart_element,
        dc_element='instantations'
    )
    if generation == 'Print':
        instantiations_element.attrib["relationship"] = 'object'
    else:
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
        if not generation == 'Print':
            counter += 1
    return instantiation_element_list


def techncial_metadata(package_info, AssetPart_element, csv_record):
    '''
    Create technical metadata for instantiations
    '''
    instantiation_counter = 1
    for package in package_info:
        for sub_item in sorted(package.keys(), reverse=True):

            if sub_item == 'Access' or sub_item == 'Preservation' or sub_item == 'Print' or sub_item == 'Preservation_01' or sub_item == 'Access_01':
                if sub_item == 'Preservation_01':
                    instantation_generation = 'Preservation'
                elif sub_item == 'Access_01':
                    instantation_generation = 'Access'
                else:
                    instantation_generation = sub_item
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
                ) = create_instantiations(AssetPart_element, instantiation_counter, generation=instantation_generation)
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
                if not fileExtension.text.lower() == 'pdf':
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
                elif sub_item == 'Print':
                    derivedFrom.text = 'Bound from multiple tiff files'
                    md5.text = extract_checksum(package['print_checksum'])
                elif sub_item == 'Preservation_01':
                    derivedFrom.text = csv_record['Object Identifier']
                    md5.text = extract_checksum(package['Preservation_01_md5'])
                elif sub_item == 'Access_01':
                    derivedFrom.text = os.path.basename(package['Preservation'])
                    md5.text = extract_checksum(package['Access_01_md5'])
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
        if not sub_item == 'Print':
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
    print('\n- California Revealed Project Dublin Core Metadata Generator - v0.18')
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
                    # check for macroman characters
                    csv_record = check_for_macroman(csv_record)
                    for values in csv_record:
                        # Check if any CSV values have unnecessary quotes and equals signs.
                        if '=' in csv_record[values]:
                            if csv_record[values][0:2] == '=\"':
                                csv_record[values] = csv_record[values][2:][:-1]
                    root_metadata_element, dublin_core_object, contributor, title = add_DC_metadata(
                        folder,
                        dc_namespace,
                        xsi_namespace,
                        csv_record
                    )
                    # Quick and dirty hack to move the created element below the creator element :(
                    contributor_index = contributor.getparent().index(contributor)
                    title_index = title.getparent().index(title)
                    created = create_dc_element(
                            index=contributor_index + 1,
                            parent=root_metadata_element,
                            dc_element='date',
                            dublin_core_namespace=dc_namespace
                        )
                    created.attrib["type"] = 'dcterms:created'
                    alternative_title = create_dc_element(
                            index=title_index + 1,
                            parent=root_metadata_element,
                            dc_element='title',
                            dublin_core_namespace=dc_namespace
                        )
                    # end of quick/dirty hack :(((
                                       # why is there an equals character and quotes in the CSV?
                    created.text = csv_record['Date Created']
                    alternative_title.attrib["type"] = 'dcterms:alternative'
                    alternative_title.text = csv_record['Additional Title']
                    (objectIdentifier,
                     callNumber,
                     projectIdentifier,
                     assetType
                    ), AssetPart_element = add_asset_elements(root_metadata_element)
                    callNumber.text = csv_record['Call Number']
                    callNumber.attrib["type"] = 'callNumber'
                    projectIdentifier.text = csv_record['Project Identifier']
                    projectIdentifier.attrib["type"] = 'projectIdentifier'
                    objectIdentifier.text = csv_record['Object Identifier']
                    objectIdentifier.attrib["type"] = 'objectIdentifier'
                    assetType.text = csv_record['Asset Type']
                    assetType.attrib["type"] = 'assetType'
                    techncial_metadata(package_info, AssetPart_element, csv_record)
                    # This will delete any collapsed, empty elements, such as </description>.
                    # all empty elements should now hopefully be deleted
                    for element in root_metadata_element.xpath(".//*"):
                        if element.text == '':
                            element.getparent().remove(element)
                    for element in root_metadata_element.xpath(".//*[not(node())]"):
                        element.getparent().remove(element)
                    with open(os.path.join(full_folder_path, csv_record['Object Identifier']) + '_metadata.xml', 'w') as outFile:
                        dublin_core_object.write(outFile, xml_declaration=True, encoding='UTF-8', pretty_print=True)
    print('- Finished')


if __name__ == '__main__':
    main()
