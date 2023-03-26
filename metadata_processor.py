import sys
import os
from xml.dom import minidom
from xml.etree import ElementTree
import xml.etree.ElementTree as ET
import pandas as PD
import hashlib
import exiftool
import time


# makes the output xml look properly structured when saved
def prettify(elem):
    rough_string = ElementTree.tostring(elem, 'utf-8')
    reparse = minidom.parseString(rough_string)
    return reparse.toprettyxml(indent="    ")

def camelCase(elem):
    metadata_string = elem
    if "-" in metadata_string:
        metadata_string = metadata_string.replace("-", " ")
    if " " in metadata_string:
        metadata_string = metadata_string.title().replace(" ", "")
        metadata_string = metadata_string[0].lower() + metadata_string[1:]
    metadata_string = metadata_string.replace("Is", "is")
    return metadata_string
# actual checksum creator. keyed on md5 but can be configured for any checksum method
def checksummer(named_file):
    md5_hash = hashlib.md5()
    blocksize = 65536
    with open(named_file, "rb") as f:
        buffer = f.read(blocksize)
        while len(buffer) > 0:
            md5_hash.update(buffer)
            buffer = f.read(blocksize)
    fixity = md5_hash.hexdigest()
    return fixity


# function to create a checksum of a file and compare to saved md5 file. Will create an md5 file is none exists
def checksum_checker(actual_file, error_log):
    md5_value2 = checksummer(actual_file)
    plain_filename = actual_file.split("/")[-1]
    if os.path.isfile(f"{actual_file}.md5"):
        with open(f"{actual_file}.md5") as r:
            for line in r:
                line = line[:-1]
                md5_value = line.split(" ")[0]
        if md5_value == md5_value2:
            print(f"hash value of {plain_filename} verified")
            return md5_value2
        else:
            print(f"checksum failure at {plain_filename}, exiting script")
            sys.exit()
    else:
        error_log.write(f"checksum file for {plain_filename} does not exist\n")
        print(f"checksum file for {plain_filename} does not exist, moving on")
        return "no information available"


# takes a single row from spreadsheet dataframe and converts it to a dictionary with the column name as the key
def row_converter(original_row=tuple, column_list=list, verbose=True):
    count = 1
    pictionary = {}
    pictionary['Index'] = original_row[0]
    for item in column_list:
        pictionary[item] = original_row[count]
        count += 1
    if verbose is True:
        print(f'your data is: {pictionary}')
    return pictionary


# function takes the supplied spreadsheet filename and creates a dataframe based on whether it is an excel file or csv

def data_frame_builder(spreadsheet_name):
    # file check
    if not os.path.isfile(spreadsheet_name):
        print(f"cannot identify the file {spreadsheet_name} for some reason")
    filetype = spreadsheet_name[-4:]
    option1 = ['.xls', 'xlsx']
    option2 = ['.csv']
    dataframe = ""
    if filetype in option1:
        dataframe = PD.read_excel(spreadsheet_name, dtype=object)
    elif filetype in option2:
        dataframe = PD.read_csv(spreadsheet_name, dtype=object)
    else:
        print("tried identifying spreadsheet using file extension, failed; trying automated loading")
        try:
            dataframe = PD.read_excel(spreadsheet_name, dtype=object)
        except:
            try:
                dataframe = PD.read_csv(spreadsheet_name, dtype=object)
            except:
                print("tried to load unsupported file type, exiting script")
                sys.exit()
    print("spreadsheet loaded")
    return dataframe


# takes dictionary of spreadsheet column/value pairs and inserts the metadata tag to be associated with the column as
# item 1, item 2 is the value of the column in the spreadsheet. 'Order' is used to re-arrange the dictionary into
# preferred tag order
def dcterms_mapper(metadata_dict=dict, mapping_dict=dict, order=list):
    if 'obj_related_materials__relation_type' in metadata_dict:
        temp_value = str(metadata_dict['obj_related_materials__relation_type'])
    for key in metadata_dict:
        if key in mapping_dict:
            metadata_dict[key] = [mapping_dict[key], str(metadata_dict[key])]
    if temp_value != "nan" and temp_value != "" and 'obj_related_materials__entity_reference' in metadata_dict:
        metadata_dict['obj_related_materials__entity_reference'][0] = "dcterms:" + str(metadata_dict['obj_related_materials__relation_type'])
    new_dict = {}
    for item in order:
        if item in metadata_dict.keys():
            new_dict[item] = metadata_dict[item]
    return new_dict


# iterates over extracted exif data and list of tags provided to. Returns the values of the first match. If no match
# returns a dummy value to help identify what should be removed
def metadata_selector(tag_list=list, tags=dict):
    value = "no information available"
    for item in tag_list:
        if item in tags.keys():
            value = tags[item]
            return value
    return value


# function to extract data using exiftool and create a dictionary of elements to add to the xml. Called for each file
# that will be included in the metadata. Uses a list of possible elements in the metadata_selector function to get the
# right data. If none of the listed tags are in the exif data, a dummy value is inserted. Dummy value later used to
# identify what items need to be removed from the dictionary
# noinspection PyTypeChecker
def exif_worker(to_characterize, checksum, error_log):
    new_dict = {}
    with exiftool.ExifToolHelper() as et:
        exif_dict = et.execute_json(to_characterize)
    exif_dict = exif_dict[0]
    print(exif_dict)
    new_dict['creationDate'] = str(
        metadata_selector(['PDF:CreateDate', 'XMP:CreationDate', 'XMP:CreateDate', 'EXIF:CreateDate',
                           'Composite:DateTimeCreated', 'File:FileCreateDate'],
                          exif_dict)[:19].replace("-", "").replace(":", "-", 2))
    # if date is no good, use date of modification as it may be more accurate than date of creation
    if len(new_dict['creationDate'].split("-")[0]) != 4:
        print("date of creation property error, using system modification date")
        new_dict['creationDate'] = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(os.path.getmtime(to_characterize)))
    new_dict['fileExtension'] = str(metadata_selector(['File:FileTypeExtension'], exif_dict))
    new_dict['standardAndFileWrapper'] = str(metadata_selector(['XMP:Format', 'File:MIMEType'], exif_dict))
    new_dict['size'] = str(round(os.path.getsize(to_characterize) / 1024 / 1024, 2))
    if 'EXIF:BitsPerSample' in exif_dict:
        if type(exif_dict['EXIF:BitsPerSample']) is int:
            exif_dict['EXIF:BitsPerSample'] = str(exif_dict['EXIF:BitsPerSample'])
        elif len(exif_dict['EXIF:BitsPerSample']) > 1:
            try:
                quickMath = exif_dict['EXIF:BitsPerSample'].split(" ")
                quickMath2 = 0
                for digit in quickMath:
                    quickMath2 += int(digit)
            except:
                quickMath = int(exif_dict['File:BitsPerSample']) * int(exif_dict['File:ColorComponents'])
                quickMath2 = str(quickMath)
            new_dict['bitDepth'] = str(quickMath2)
        else:
            new_dict['bitDepth'] = exif_dict['EXIF:BitsPerSample']
    new_dict['pageNumber'] = str(metadata_selector(['File:PageCount', 'EXIF:PageNumber', 'PDF:PageCount','XMP:PageNumber', 'XML:Pages'], exif_dict))
    # new_dict['hasThumbnail'] = str(metadata_selector(['EXIF:ThumbnailImage', 'XMP:Thumbnails', 'Photoshop:PhotoshopThumbnail', 'JFIF:ThumbnailImage'], exif_dict))
    # if new_dict['hasThumbnail'] != "no information available":
    #    new_dict['hasThumbnail'] = "True"
    new_dict['imageWidth'] = str(metadata_selector(['EXIF:ImageWidth', 'File:ImageWidth'], exif_dict))
    new_dict['imageLength'] = str(metadata_selector(['EXIF:ImageHeight', 'File:ImageHeight'], exif_dict))
    if to_characterize.endswith(".tif"):
        new_dict['compression'] = str(metadata_selector(['EXIF:Compression'], exif_dict))
        if new_dict['compression'] == "1":
            new_dict['compression'] = "Uncompressed"
        if new_dict['compression'] == "5":
            new_dict['compression'] = "LZW"
    if to_characterize.endswith(".jpg"):
        new_dict['compression'] = str(metadata_selector(['File:FileType'], exif_dict))
    new_dict['samplesPerPixel'] = str(metadata_selector(['EXIF:SamplesPerPixel', 'File:ColorComponents'], exif_dict))
    new_dict['xResolution'] = str(metadata_selector(['EXIF:XResolution', 'JFIF:XResolution'], exif_dict))
    new_dict['yResolution'] = str(metadata_selector(['EXIF:YResolution', 'JFIF:YResolution'], exif_dict))
    new_dict['md5'] = checksum_checker(to_characterize, error_log)
    new_dict['creatingApplicationAndVersion'] = metadata_selector(['EXIF:Software', 'XMP:CreatorTool', 'PDF:Creator', 'XMP:HistorySoftwareAgent', 'XML:Application'],
                                                                  exif_dict)
    if type(new_dict['creatingApplicationAndVersion']) is list:
        new_dict['creatingApplicationAndVersion'] = new_dict['creatingApplicationAndVersion'][0]
    if type(new_dict['creatingApplicationAndVersion']) is not list and new_dict['creatingApplicationAndVersion'].startswith("#") and "Comment" in new_dict[
        'creatingApplicationAndVersion']:
        man_data = new_dict['creatingApplicationAndVersion'].split("Comment=")[1].split("\n")[0]
        if "FirmwareVersion" in new_dict['creatingApplicationAndVersion']:
            man_data = man_data + " Firmware version " + \
                       new_dict['creatingApplicationAndVersion'].split('FirmwareVersion=')[1].split("\n")[0]
        new_dict['creatingApplicationAndVersion'] = man_data
    new_dict['derivedFrom'] = "placeholder"
    new_dict['digitalManufacturer'] = metadata_selector(['EXIF:Make'], exif_dict)
    new_dict['digitizerModel'] = metadata_selector(['EXIF:Model'], exif_dict)
    new_dict['imageProducer'] = metadata_selector(['XMP:Artist', 'EXIF:Artist', 'XMP:Creator','XMP:Author'], exif_dict)
    to_remove = []
    for key in new_dict.keys():
        # clean up unnecessary line breaks
        if "\n" in new_dict[key]:
            new_dict[key] = new_dict[key].replace("\n", ", ")
        if new_dict[key] == "no information available":
            to_remove.append(key)
    for item in to_remove:
        del new_dict[item]
    return new_dict

def size_eval(file_size):
    size = round(os.path.getsize(file_size) / 1024 / 1024, 2)
    if size < 1:
        size = str(round(os.path.getsize(file_size) / 1024, 2))
        return [size,'kilobytes']
    else:
        return [str(size), 'megabytes']

# the mapping of spreadsheet columns to Qualified Dublin Core elements
dcterms_mapping_dict = {
    'Index': 'dcterms:Index',
    'label': 'dcterms:title',
    'obj_alternative_title': "dcterms:alternative",
    'obj_series_title': 'dcterms:alternative',
    'obj_created_date__date_free': 'dcterms:created',
    'obj_published_date__date_free': 'dcterms:issued',
    'obj_creator__name_label_creator_role': 'dcterms:creator',
    'obj_creator__name_label_annotator_role': 'dcterms:creator',
    'obj_creator__name_label_artist_role': 'dcterms:creator',
    'obj_creator__name_label_cartographer_role': 'dcterms:creator',
    'obj_creator__name_label_correspondent_role': 'dcterms:creator',
    'obj_creator__name_label_designer_role': 'dcterms:creator',
    'obj_creator__name_label_donor_role': 'dcterms:creator',
    'obj_creator__name_label_editor_role': 'dcterms:creator',
    'obj_creator__name_label_interviewee_role': 'dcterms:creator',
    'obj_creator__name_label_interviewer_role': 'dcterms:creator',
    'obj_creator__name_label_photographer_role': 'dcterms:creator',
    'obj_creator__name_label_transcriber_role': 'dcterms:creator',
    'obj_creator__name_label_translator_role': 'dcterms:creator',
    'obj_creator__name_label_contributor_role': 'dcterms:contributor',
    'obj_creator__name_label_publisher_role': 'dcterms:publisher',
    'obj_publication_location__label': 'dcterms:location',
    'obj_description': 'dcterms:description',
    'obj_container_item_annotations': 'dcterms:description',
    'obj_copyright_statement': 'dcterms:RightsStatement',
    'obj_copyright_date__date_free': 'dcterms:dateCopyrighted',
    'obj_related_materials__entity_reference': 'dcterms:relatedTo',
    'obj_media_type': 'dcterms:type',
    'obj_collection_guide__title': 'dcterms:isPartOf',
    'obj_collection_guide__url': 'dcterms:isPartOf',
    'obj_copyright_notice': 'dcterms:rightsNote',
    'obj_creator__name_label_copyright_holder_role': 'dcterms:rightsHolder',
    'obj_copyright_holder_info': 'dcterms:rightsHolder',
    'obj_print_item_parts__ip_print_format': 'dcterms:medium',
    'obj_print_item_parts__ip_generation': 'dcterms:format',
    'obj_print_item_parts__ip_extent': 'dcterms:extent',
    'obj_print_item_parts__ip_ext_dim': 'dcterms:extent',
    'obj_significance': 'dcterms:ProvenanceStatement',
    'obj_condition_list__value': 'dcterms:ProvenanceStatement',
    'obj_condition_note': 'dcterms:ProvenanceStatement',
    'obj_add_tech_notes': 'dcterms:ProvenanceStatement',
    'obj_notes_to_vendor': 'dcterms:ProvenanceStatement',
    'obj_car_notes_for_partner': 'dcterms:ProvenanceStatement',
    'obj_partner_admin_notes': 'dcterms:ProvenanceStatement',
    'obj_administrative_notes': 'dcterms:ProvenanceStatement',
    'obj_project_note': 'dcterms:provenance',
    'obj_funder': 'dcterms:ProvenanceStatement',
    'obj_grant_cycle': 'dcterms:dateAccepted',
    'marc': 'dcterms:provenance',
    'obj_partner_name': 'dcterms:provenance',
    'obj_partner_websites': 'dcterms:provenance',
    'obj_partner_rights_statement': 'dcterms:provenance',
    'obj_partner_address': 'dcterms:location',
    'obj_subject_topic__label': 'dcterms:subject',
    'obj_subject_entity__label': 'dcterms:subject',
    'obj_spatial_coverage__label': 'dcterms:spatial',
    'obj_temporal_coverage__date_free': 'dcterms:temporal',
    'obj_language__value': 'dcterms:language',
    'obj_country_of_creation__value': 'dcterms:location',
    'obj_object_identifier': 'dcterms:identifier',
    'obj_temporary_id': 'dcterms:identifier',
    'obj_call_number': 'dcterms:identifier',
    'obj_project_identifier': 'dcterms:identifier',
    'obj_ia_url__url': 'dcterms:identifier',
    'obj_nid_link': 'dcterms:identifier',
    'node_id_no_changes': 'dcterms:identifier',
    'node_uuid_no_changes': 'dcterms:identifier',
    'obj_serial_volume': 'dcterms:identifier',
    'obj_serial_issue': 'dcterms:identifier',
    'obj_node_id_from_d7': 'dcterms:identifier',
    'obj_ark_identifier': 'dcterms:identifier',
    'obj_oclc_number': 'dcterms:identifier',
    'obj_cdnp_identifier': 'dcterms:identifier',
    'obj_notes_from_vendor': 'dcterms:ProvenanceStatement'
}
# mapping of spreadsheet columns to attributes to give nuance to Dublin Core. NOT for Qualified Dublin Core
dc_attrib_dict = {
    'label': 'main',
    'obj_alternative_title': 'dcterms:alternative',
    'obj_series_title': 'series',
    'obj_created_date__date_free': 'dcterms:created',
    'obj_published_date__date_free': 'dcterms:issued',
    'obj_creator__name_label_creator_role': 'creator',
    'obj_creator__name_label_annotator_role': 'annotator',
    'obj_creator__name_label_artist_role': 'artist',
    'obj_creator__name_label_cartographer_role': 'cartographer',
    'obj_creator__name_label_correspondent_role': 'correspondent',
    'obj_creator__name_label_designer_role': 'designer',
    'obj_creator__name_label_donor_role': 'donor',
    'obj_creator__name_label_editor_role': 'editor',
    'obj_creator__name_label_interviewee_role': 'interviewee',
    'obj_creator__name_label_interviewer_role': 'interviewer',
    'obj_creator__name_label_photographer_role': 'photographer',
    'obj_creator__name_label_transcriber_role': 'transcriber',
    'obj_creator__name_label_translator_role': 'translator',
    'obj_publication_location__label': 'dcterms:location',
    'obj_description': 'contentSummary',
    'obj_container_item_annotations': 'annotation',
    'obj_copyright_statement': 'copyrightStatement',
    'obj_copyright_date__date_free': 'dateCopyrighted',
    'obj_collection_guide__title': 'isPartOf',
    'obj_collection_guide__url': 'isPartOf',
    'obj_copyright_notice': 'rightsNote',
    'obj_creator__name_label_copyright_holder_role': 'rightsHolder',
    'obj_copyright_holder_info': 'rightsHolder',
    'obj_print_item_parts__ip_print_format': 'dcterms:medium',
    'obj_print_item_parts__ip_generation': 'dcterms:format',
    'obj_print_item_parts__ip_extent': 'dcterms:extent',
    'obj_print_item_parts__ip_ext_dim': 'dcterms:extent',
    'obj_significance': 'significance',
    'obj_condition_list__value': 'condition',
    'obj_condition_note': 'condition',
    'obj_add_tech_notes': 'additionalTechnical',
    'obj_notes_to_vendor': 'noteToVendor',
    'obj_car_notes_for_partner': 'noteForPartner',
    'obj_partner_admin_notes': 'institution',
    'obj_administrative_notes': 'administrativeNotes',
    'obj_project_note': 'projectNote',
    'obj_funder': 'fundedBy',
    'obj_grant_cycle': 'dcterms:dateAccepted',
    'marc': 'marc',
    'obj_partner_name': 'partnerName',
    'obj_partner_websites': 'institutionURL',
    'obj_partner_rights_statement': 'partnerRights',
    'obj_partner_address': 'institutionAddress',
    'obj_subject_topic__label': 'topic',
    'obj_subject_entity__label': 'entity',
    'obj_spatial_coverage__label': 'spatial',
    'obj_temporal_coverage__date_free': 'temporal',
    'obj_country_of_creation__value': 'spatialCountry',
    'obj_object_identifier': 'objectIdentifier',
    'obj_temporary_id': 'temporaryIdentifier',
    'obj_call_number': 'callNumber',
    'obj_project_identifier': 'projectIdentifier',
    'obj_ia_url__url': 'IAurl',
    'obj_nid_link': 'NIDUrl',
    'node_id_no_changes': 'changesIdentifier',
    'node_uuid_no_changes': 'changesUUID',
    'obj_serial_volume': 'volume',
    'obj_serial_issue': 'issue',
    'obj_node_id_from_d7': 'nodeIdentifier',
    'obj_ark_identifier': 'arkIdentifier',
    'obj_oclc_number': 'OCLC',
    'obj_cdnp_identifier': 'CDNP',
    'obj_notes_from_vendor': 'notesFromVendor'
}
# the mapping of spreadsheet columns to dublin core elements
dc_mapping_dict = {
    'Index': 'dc:Index',
    'label': 'dc:title',
    'obj_alternative_title': "dc:title",
    'obj_series_title': 'dc:title',
    'obj_created_date__date_free': 'dc:date',
    'obj_published_date__date_free': 'dcterms:issued',
    'obj_creator__name_label_creator_role': 'dc:creator',
    'obj_creator__name_label_annotator_role': 'dc:creator',
    'obj_creator__name_label_artist_role': 'dc:creator',
    'obj_creator__name_label_cartographer_role': 'dc:creator',
    'obj_creator__name_label_correspondent_role': 'dc:creator',
    'obj_creator__name_label_designer_role': 'dc:creator',
    'obj_creator__name_label_donor_role': 'dc:creator',
    'obj_creator__name_label_editor_role': 'dc:creator',
    'obj_creator__name_label_interviewee_role': 'dc:creator',
    'obj_creator__name_label_interviewer_role': 'dc:creator',
    'obj_creator__name_label_photographer_role': 'dc:creator',
    'obj_creator__name_label_transcriber_role': 'dc:creator',
    'obj_creator__name_label_translator_role': 'dc:creator',
    'obj_creator__name_label_contributor_role': 'dc:contributor',
    'obj_creator__name_label_publisher_role': 'dc:publisher',
    'obj_publication_location__label': 'dcterms:location',
    'obj_description': 'dc:description',
    'obj_container_item_annotations': 'dc:description',
    'obj_copyright_statement': 'dc:rights',
    'obj_copyright_date__date_free': 'dcterms:dateCopyrighted',
    'obj_related_materials__entity_reference': 'dc:relatedTo',
    'obj_media_type': 'dc:type',
    'obj_collection_guide__title': 'dc:relation',
    'obj_collection_guide__url': 'dc:relation',
    'obj_copyright_notice': 'dc:rights',
    'obj_creator__name_label_copyright_holder_role': 'dc:rights',
    'obj_copyright_holder_info': 'dc:rights',
    'obj_print_item_parts__ip_print_format': 'dc:format',
    'obj_print_item_parts__ip_generation': 'dc:format',
    'obj_print_item_parts__ip_extent': 'dc:format',
    'obj_print_item_parts__ip_ext_dim': 'dc:format',
    'obj_significance': 'dc:provenance',
    'obj_condition_list__value': 'dc:provenance',
    'obj_condition_note': 'dc:provenance',
    'obj_add_tech_notes': 'dc:description',
    'obj_notes_to_vendor': 'dc:provenance',
    'obj_car_notes_for_partner': 'dc:provenance',
    'obj_partner_admin_notes': 'dc:provenance',
    'obj_administrative_notes': 'dc:provenance',
    'obj_project_note': 'dc:provenance',
    'obj_funder': 'dc:provenance',
    'obj_grant_cycle': 'dc:date',
    'marc': 'dc:identifier',
    'obj_partner_name': 'dc:provenance',
    'obj_partner_websites': 'dc:provenance',
    'obj_partner_rights_statement': 'dc:rights',
    'obj_partner_address': 'dc:provenance',
    'obj_subject_topic__label': 'dc:subject',
    'obj_subject_entity__label': 'dc:subject',
    'obj_spatial_coverage__label': 'dc:coverage',
    'obj_temporal_coverage__date_free': 'dc:coverage',
    'obj_language__value': 'dc:language',
    'obj_country_of_creation__value': 'dc:coverage',
    'obj_object_identifier': 'dc:identifier',
    'obj_temporary_id': 'dc:identifier',
    'obj_call_number': 'dc:identifier',
    'obj_project_identifier': 'dc:identifier',
    'obj_ia_url__url': 'dc:identifier',
    'obj_nid_link': 'dc:identifier',
    'node_id_no_changes': 'dc:identifier',
    'node_uuid_no_changes': 'dc:identifier',
    'obj_serial_volume': 'dc:identifier',
    'obj_serial_issue': 'dc:identifier',
    'obj_node_id_from_d7': 'dc:identifier',
    'obj_ark_identifier': 'dc:identifier',
    'obj_oclc_number': 'dc:identifier',
    'obj_cdnp_identifier': 'dc:identifier',
    'obj_notes_from_vendor': 'dc:provenance'
}
# a list designating the order in which elements will appear
ordered_dict = ['Index',
                'label',
                'obj_alternative_title',
                'obj_series_title',
                'obj_created_date__date_free',
                'obj_published_date__date_free',
                'obj_creator__name_label_creator_role',
                'obj_creator__name_label_annotator_role',
                'obj_creator__name_label_artist_role',
                'obj_creator__name_label_cartographer_role',
                'obj_creator__name_label_correspondent_role',
                'obj_creator__name_label_designer_role',
                'obj_creator__name_label_donor_role',
                'obj_creator__name_label_editor_role',
                'obj_creator__name_label_interviewee_role',
                'obj_creator__name_label_interviewer_role',
                'obj_creator__name_label_photographer_role',
                'obj_creator__name_label_transcriber_role',
                'obj_creator__name_label_translator_role',
                'obj_creator__name_label_contributor_role',
                'obj_creator__name_label_publisher_role',
                'obj_publication_location__label',
                'obj_description',
                'obj_container_item_annotations',
                'obj_copyright_statement',
                'obj_copyright_date__date_free',
                'obj_creator__name_label_copyright_holder_role',
                'obj_copyright_holder_info',
                'obj_copyright_notice',
                'obj_collection_guide__title',
                'obj_collection_guide__url',
                'obj_related_materials__entity_reference',
                'obj_media_type',
                'obj_print_item_parts__ip_print_format',
                'obj_print_item_parts__ip_generation',
                'obj_print_item_parts__ip_extent',
                'obj_print_item_parts__ip_ext_dim',
                'obj_significance',
                'obj_condition_list__value',
                'obj_condition_note',
                'obj_add_tech_notes',
                'obj_notes_to_vendor',
                'obj_car_notes_for_partner',
                'obj_partner_admin_notes',
                'obj_administrative_notes',
                'obj_project_note',
                'obj_funder',
                'obj_grant_cycle',
                'marc',
                'obj_partner_name',
                'obj_partner_websites',
                'obj_partner_rights_statement',
                'obj_partner_address',
                'obj_subject_topic__label',
                'obj_subject_entity__label',
                'obj_spatial_coverage__label',
                'obj_temporal_coverage__date_free',
                'obj_language__value',
                'obj_country_of_creation__value',
                'obj_object_identifier',
                'obj_temporary_id',
                'obj_call_number',
                'obj_project_identifier',
                'obj_ia_url__url',
                'obj_nid_link',
                'node_id_no_changes',
                'node_uuid_no_changes',
                'obj_serial_volume',
                'obj_serial_issue',
                'obj_node_id_from_d7',
                'obj_ark_identifier',
                'obj_oclc_number',
                'obj_cdnp_identifier',
                'obj_notes_from_vendor']

spreadsheet = input("enter spreadsheet name including filepath: ")
while spreadsheet.endswith(" "):
    spreadsheet = spreadsheet[:-1]
launchpad = input("enter root folder filepath: ")
while launchpad.endswith(" "):
    launchpad = launchpad[:-1]
export_type = input("type 'dcterms' for qualified dublin core, type 'dc' for simple dublin core: ")

try:
    exif_data = exiftool.ExifToolHelper(spreadsheet)
except:
    print("need exiftool location")
    exe = input("enter exiftool location: ")
    exiftool.ExifTool(exe)
# exiftool_path = input("path to exiftool: ")

df = data_frame_builder(spreadsheet)
log_name = spreadsheet.split("/")[-1].split("\\")[-1].split(".")[0]
error_log = open(f"{launchpad}/qualified_dublinCore_error_log_{log_name}.txt", "a")
general_log = open(f"{launchpad}/qualified_dublinCore_export_log_{log_name}.txt", "a")
listy = df.columns
for row in df.itertuples():
    valuables = row_converter(row, listy, verbose=False)
    #print(f"Beginning {valuables['obj_object_identifier']}")
    general_log.write(f"***{valuables['obj_object_identifier']}***\n")
    error_log.write(f"***{valuables['obj_object_identifier']}***\n")
    if export_type == 'dcterms':
        valuables = dcterms_mapper(valuables, dcterms_mapping_dict, ordered_dict)
    if export_type == "dc":
        valuables = dcterms_mapper(valuables, dc_mapping_dict, ordered_dict)
    metadata = ET.Element('metadata')
    if export_type == "dcterms":
        metadata.set('xmlns', 'http://purl.org/dc/terms/')
    if export_type == "dc":
        metadata.set("xmlns", 'http://purl.org/dc/elements/1.1/')
    metadata.set('xmlns:xsi', 'http://www.w3.org/2001/XMLSchema-instance')
    metadata.set('xsi:schemaLocation',
                 'http://purl.org/dc/terms/ https://repository.californiarevealed.org/sites/default/files/2022-04/CA-Rdqdcterms.xsd')
    metadata.set('xmlns:dcterms', 'http://purl.org/dc/terms/')
    metadata.set('xmlns:dc', 'http://purl.org/dc/elements/1.1/')
    exceptions = ['Index',
                  'obj_notes_from_vendor',
                  'Embedded Title',
                  'Embedded Institution',
                  'Embedded Comment',
                  'Embedded Copyright']
    #print("metadata dictionary prepared, processing xml")
    for key in valuables:
        if key not in exceptions:
            if valuables[key][-1] != 'nan':
                something = valuables[key][0]
                if ";" in valuables[key][-1]:
                    split_list = valuables[key][-1].split(";")
                    if ";" in valuables[key][0]:
                        prefix = valuables[key][0].split(":")[0]
                        tag_list = valuables[key][0].split(":")[1].split(";")
                        tag_count = 0
                        for item in tag_list:
                            thingy = ET.SubElement(metadata, f'{prefix}:{camelCase(item)}')
                            thingy.text = split_list[tag_count]
                            tag_count += 1
                    else:
                        for item in split_list:
                            thingy = ET.SubElement(metadata, camelCase(valuables[key][0]))
                            thingy.text = item
                            if export_type == 'dc' and key in dc_attrib_dict:
                                thingy.attrib['type'] = dc_attrib_dict[key]
                else:
                    thingy = ET.SubElement(metadata, camelCase(valuables[key][0]))
                    thingy.text = valuables[key][-1]
                    # take care of unnecessary line breaks
                    if '\n' in thingy.text:
                        thingy2 = thingy.text
                        thingy2 = thingy2.replace("\n", ", ")
                        thingy.text = thingy2
                    if export_type == 'dc' and key in dc_attrib_dict:
                        thingy.attrib['type'] = dc_attrib_dict[key]
                        if dc_attrib_dict[key] == 'IAurl':
                            thingy.attrib['xsi:type'] = 'dcterms:URI'
    assets = ET.SubElement(metadata, 'Assets')
    if export_type == "dcterms":
        if valuables['obj_object_identifier'][-1] != "nan":
            sub_id = ET.SubElement(assets, 'dcterms:identifier')
            sub_id.text = valuables['obj_object_identifier'][-1]
        if valuables['obj_call_number'][-1] != "nan":
            sub_id2 = ET.SubElement(assets, 'dcterms:identifer')
            sub_id2.text = valuables['obj_call_number'][-1]
        if valuables['obj_project_identifier'][-1] != "nan":
            sub_id3 = ET.SubElement(assets, 'dcterms:identifier')
            sub_id3.text = valuables['obj_project_identifier'][-1]
        if valuables['obj_notes_from_vendor'][-1] != "nan":
            assets_prov = ET.SubElement(assets, 'dcterms:ProvenanceStatement')
            assets_prov.text = valuables['obj_notes_from_vendor'][-1]
        if valuables['obj_notes_from_vendor'] == "nan":
            print("no vendor provenance statement")
    if export_type == "dc":
        if valuables['obj_object_identifier'][-1] != "nan":
            sub_id = ET.SubElement(assets, 'dc:identifier')
            sub_id.attrib['type'] = "objectIdentifier"
            sub_id.text = valuables['obj_object_identifier'][-1]
        if valuables['obj_call_number'][-1] != "nan":
            sub_id2 = ET.SubElement(assets, 'dc:identifier')
            sub_id2.attrib['type'] = "callNumber"
            sub_id2.text = valuables['obj_call_number'][-1]
        if valuables['obj_notes_from_vendor'][-1] != "nan":
            sub_id3 = ET.SubElement(assets, 'dc:identifier')
            sub_id3.attrib['type'] = "projectIdentifier"
            sub_id3.text = valuables['obj_project_identifier'][-1]
        if valuables['obj_notes_from_vendor'][-1] != "nan":
            assets_prov = ET.SubElement(assets, 'dc:provenance')
            assets_prov.attrib['type'] = 'notesFromVendor'
            assets_prov.text = valuables['obj_notes_from_vendor'][-1]
        if valuables['obj_notes_from_vendor'] == "nan":
            print("no vendor provenance statement")
    asset_parts = ET.SubElement(assets, 'AssetPart')
    general_log.write("standard metadata could be compiled\n")
    directory = launchpad + "/" + valuables['obj_object_identifier'][-1]
    preservation_files = []
    presentation_files = []
    mezzanine_files = []
    access_files = []
    ext_list = ""
    ext_list = set()
    pdf_counter = 0
    multi_page = 0
    exclusion_list = ['md5', 'xml','DS_Store']
    for dirpath, dirnames, filenames in os.walk(directory):
        for filename in filenames:
            if filename.split(".")[-1] not in exclusion_list:
                filename2 = filename.split(".")[-2]
                with exiftool.ExifToolHelper() as et:
                    exif_dict = et.execute_json(f"{directory}/{filename}")
                exif_dict = exif_dict[0]
                filetype = exif_dict['File:MIMEType'].split("/")[0]
                # use file type to determine what method to use
                if "EXIF:PageNumber" in exif_dict and exif_dict['EXIF:PageNumber'] != "0 0":
                    access_files.append(filename)
                    ext_list.add(filename.split(".")[-1].lower())
                    multi_page += 1
                elif filename2.endswith("_prsv") and filetype == 'image':
                    preservation_files.append(filename)
                elif filename2.endswith("_prsv") and exif_dict['File:MIMEType'] == 'application/vnd.adobe.photoshop':
                    preservation_files.append(filename)
                elif filename2.endswith("_prsv") and exif_dict['File:MIMEType'] == 'application/pdf':
                    preservation_files.append(filename)
                elif filename2.endswith("_mezz") and filetype == 'image':
                    mezzanine_files.append(filename)
                elif filename2.endswith("_access") and filetype == 'image':
                    presentation_files.append(filename)
                else:
                    access_files.append(filename)
                    if "_prsv" in filename:
                        ext_list.add(filename.split(".")[-1].lower())
                        pdf_counter += 1
    preservation_files.sort()
    presentation_files.sort()
    access_files.sort()
    temp_list1 = []
    for item in preservation_files:
        item = item.split(".")[0].replace("_prsv", "")
        temp_list1.append(item)
    for item in presentation_files:
        temp = item.split(".")[0].replace("_access", "")
        if temp not in temp_list1:
            error_log.write(f"missing preservation file for: {item}\n")
            print(f"presentation item {item} is standalone, noting error log")
    access_files.sort()
    counter = 0
    flag = False
    if len(preservation_files) == 1:
        flag = True
    if len(preservation_files) > 0:
        for master in preservation_files:
            print("characterizing", master)
            ext_list.add(master.split(".")[-1].lower())
            instantiations = ET.SubElement(asset_parts, "instantiations")
            counter += 1
            if flag is True:
                instantiations.attrib['relationship'] = "object"
            else:
                instantiations.attrib['relationship'] = f"page {counter}"
            instance_preservation = ET.SubElement(instantiations, "instantiation")
            instance_preservation.attrib['generation'] = "Preservation Master"
            tech_stuff = ET.SubElement(instance_preservation, 'technical')
            file_id = ET.SubElement(tech_stuff, 'digitalFileIdentifier')
            file_id.text = master
            md5 = checksummer(f"{directory}/{master}")
            exif_dict = exif_worker(f"{directory}/{master}", md5, error_log)
            for key in exif_dict:
                thingy = ET.SubElement(tech_stuff, key)
                thingy.text = exif_dict[key]
            size = tech_stuff.find('size')
            valuation = size_eval(f"{directory}/{master}")
            size.text = str(valuation[0])
            size.attrib['unit'] = valuation[1]
            if exif_dict['standardAndFileWrapper'] != "application/pdf":
                imageWidth = tech_stuff.find('imageWidth')
                imageWidth.attrib['unit'] = 'pixels'
                imageLength = tech_stuff.find('imageLength')
                imageLength.attrib['unit'] = 'pixels'
            derived = tech_stuff.find('derivedFrom')
            derived.text = valuables['obj_object_identifier'][-1]
            root_filename = master.split(".")[0].replace("_prsv", "")
            general_log.write(f"{master} processed\n")
            for mezzanine in mezzanine_files:
                mezzanine_root = mezzanine.split(".")[0].replace("_mezz", "")
                if root_filename == mezzanine_root:
                    print(f"characterizing {mezzanine}")
                    instance_mezzanine = ET.SubElement(instantiations, 'instantiation')
                    instance_mezzanine.attrib['generation'] = "Mezzanine Copy"
                    tech_stuff = ET.SubElement(instance_mezzanine, "technical")
                    file_id = ET.SubElement(tech_stuff, 'digitalFileIdentifier')
                    file_id.text = mezzanine
                    md5 = checksummer(f"{directory}/{mezzanine}")
                    exif_dict = exif_worker(f"{directory}/{mezzanine}", md5, error_log)
                    for key in exif_dict:
                        thingy = ET.SubElement(tech_stuff, key)
                        thingy.text = exif_dict[key]
                    size = tech_stuff.find('size')
                    valuation = size_eval(f"{directory}/{mezzanine}")
                    size.text = str(valuation[0])
                    size.attrib['unit'] = valuation[1]
                    imageWidth = tech_stuff.find('imageWidth')
                    imageWidth.attrib['unit'] = 'pixels'
                    imageLength = tech_stuff.find('imageLength')
                    imageLength.attrib['unit'] = 'pixels'
                    derived = tech_stuff.find('derivedFrom')
                    derived.text = master  # valuables['obj_object_identifier'][-1]
                    general_log.write(f"{mezzanine} processed\n")
            for presentation in presentation_files:
                presentation_root = presentation.split(".")[0].replace("_access", "")
                if root_filename == presentation_root:
                    print(f"characterizing {presentation}")
                    instance_presentation = ET.SubElement(instantiations, 'instantiation')
                    instance_presentation.attrib['generation'] = "Access Copy"
                    tech_stuff = ET.SubElement(instance_presentation, "technical")
                    file_id = ET.SubElement(tech_stuff, 'digitalFileIdentifier')
                    file_id.text = presentation
                    md5 = checksummer(f"{directory}/{presentation}")
                    exif_dict = exif_worker(f"{directory}/{presentation}", md5, error_log)
                    for key in exif_dict:
                        thingy = ET.SubElement(tech_stuff, key)
                        thingy.text = exif_dict[key]
                    size = tech_stuff.find('size')
                    valuation = size_eval(f"{directory}/{presentation}")
                    size.text = str(valuation[0])
                    size.attrib['unit'] = valuation[1]
                    imageWidth = tech_stuff.find('imageWidth')
                    imageWidth.attrib['unit'] = 'pixels'
                    imageLength = tech_stuff.find('imageLength')
                    imageLength.attrib['unit'] = 'pixels'
                    derived = tech_stuff.find('derivedFrom')
                    derived.text = master  # valuables['obj_object_identifier'][-1]
                    general_log.write(f"{presentation} processed\n")
    ext_list = list(ext_list)
    ext_list.sort()
    counter = 0
    if len(access_files) > 0:
        for access_file in access_files:
            print(f"characterizing {access_file}")
            instantiations = ET.SubElement(asset_parts, "instantions")
            if len(access_files) == 1:
                instantiations.attrib['relationship'] = 'object'
            else:
                counter += 1
                instantiations.attrib['relationship'] = f'File{str(counter)}'
            instance_access = ET.SubElement(instantiations, "instantiation")
            if "_prsv" in access_file:
                instance_access.attrib['generation'] = "Preservation"
            if "_access" in access_file:
                instance_access.attrib['generation'] = "Access"
            tech_stuff = ET.SubElement(instance_access, "technical")
            file_id = ET.SubElement(tech_stuff, 'digitalFileIdentifier')
            file_id.text = access_file
            md5 = checksummer(f"{directory}/{access_file}")
            exif_dict = exif_worker(f"{directory}/{access_file}", md5, error_log)
            for key in exif_dict:
                thingy = ET.SubElement(tech_stuff, key)
                thingy.text = exif_dict[key]
            size = tech_stuff.find('size')
            valuation = size_eval(f"{directory}/{access_file}")
            size.text = str(valuation[0])
            size.attrib['unit'] = valuation[1]
            imageWidth = tech_stuff.find('imageWidth')
            if imageWidth is not None:
                imageWidth.attrib['unit'] = 'pixels'
            imageLength = tech_stuff.find('imageLength')
            if imageLength is not None:
                imageLength.attrib['unit'] = 'pixels'
            derived = tech_stuff.find('derivedFrom')
            if "_prsv" in access_file:
                derived.text = valuables['obj_object_identifier'][-1]
            if "_access" in access_file:
                if len(ext_list) == 1:
                    if len(preservation_files) == 1:
                        bound_from = ['single','file']
                    if len(preservation_files) > 1:
                        bound_from = ['multiple','files']
                    if multi_page == 1:
                        bound_from = ['single multi-page', 'file']
                    if multi_page > 1:
                        bound_from = ['multiple multi-page', 'files']
                    if ext_list[0] == "pdf":
                        if pdf_counter == 1:
                            bound_from = ['single','file']
                        if pdf_counter > 1:
                            bound_from = ['multiple','files']
                if len(ext_list) > 1:
                    temp_text = ""
                    for item in ext_list:
                        temp_text = temp_text + f"{item}, "
                    temp_text = temp_text.replace(f", {ext_list[-1]}, ", f" and {ext_list[-1]}")
                    ext_list[0] = temp_text
                    bound_from = ['multiple','files']
                derived.text = f"Bound from {bound_from[0]} {ext_list[0]} {bound_from[1]}"
            general_log.write(f"{access_file} processed\n")
    metadataFile = f"{directory}/{valuables['obj_object_identifier'][-1]}_metadata.xml"
    if os.path.isdir(directory):
        with open(metadataFile, "w", encoding='UTF-8') as output:
            output.write(prettify(metadata))
        output.close()
        # manually add in encoding declaration
        with open(metadataFile, "r") as r:
            filedata = r.read()
            filedata = filedata.replace('xml version="1.0" ', 'xml version="1.0" encoding="UTF-8"')
            with open(metadataFile, "w") as w:
                w.write(filedata)
            w.close()
        general_log.write(f"{metadataFile.split('/')[-1]} generated\n")
        print(f"{metadataFile.split('/')[-1]} saved")
    else:
        print(f"{metadataFile.split('/')[-1]} cannot be saved because directory doesn't exist")
        error_log.write(f"{metadataFile.split('/')[-1]} cannot be created because directory does not exist\n")
''''<dcterms:hasFormat>458349</dcterms:hasFormat>
<dcterms:hasPart>462102</dcterms:hasPart>
'''
general_log.close()
error_log.close()

