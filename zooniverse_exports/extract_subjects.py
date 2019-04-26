""" Extract Subjects Data """
import csv
import os
import logging
import argparse
from collections import OrderedDict

import pandas as pd

from utils.logger import set_logging
from utils.utils import print_nested_dict, set_file_permission
from zooniverse_exports import extractor
from config.cfg import cfg

flags = cfg['subject_extractor_flags']

# # test
# args = dict()
# args['subject_csv'] = '/home/packerc/shared/zooniverse/Exports/MAD/MAD_S1_subjects.csv'
# args['output_csv'] = '/home/packerc/shared/zooniverse/Exports/MAD/MAD_S1_subjects_extracted.csv'


if __name__ == '__main__':

    # Parse command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("--subject_csv", type=str, required=True)
    parser.add_argument("--output_csv", type=str, required=True)
    parser.add_argument("--log_dir", type=str, default=None)
    parser.add_argument("--log_filename", type=str, default='extract_subjects')

    args = vars(parser.parse_args())

    ######################################
    # Check Input
    ######################################

    if not os.path.isfile(args['subject_csv']):
        raise FileNotFoundError("subject_csv: {} not found".format(
                                args['subject_csv']))

    ######################################
    # Configuration
    ######################################

    # logging
    set_logging(args['log_dir'], args['log_filename'])
    logger = logging.getLogger(__name__)

    # logging flags
    print_nested_dict('', flags)

    # Read Subject CSV
    n_images_per_subject = list()
    subject_info = OrderedDict()
    subject_data_header = set()
    with open(args['subject_csv'], "r") as ins:
        csv_reader = csv.reader(ins, delimiter=',', quotechar='"')
        header_subject = next(csv_reader)
        row_name_to_id_mapper_sub = {x: i for i, x in enumerate(header_subject)}
        for line_no, line in enumerate(csv_reader):
            subject_id = line[row_name_to_id_mapper_sub['subject_id']]
            # Extract Location / URL Data
            locations_dict = extractor.extract_key_from_json(
                line, 'locations', row_name_to_id_mapper_sub)
            # append 'url' to key-names: 0->url0
            location_keys = list(locations_dict.keys())
            location_keys.sort()
            for i in range(0, len(location_keys)):
                locations_dict['zooniverse_url_{}'.format(i)] = \
                    locations_dict.pop('{}'.format(i))
            # extract metadata
            metadata_dict = extractor.extract_key_from_json(
                line, 'metadata', row_name_to_id_mapper_sub)
            # get other information
            retired_at = line[row_name_to_id_mapper_sub['retired_at']]
            retirement_reason = line[row_name_to_id_mapper_sub['retirement_reason']]
            # handle legacy case when 'created_at' was not in Zooniverse exports
            try:
                created_at = line[row_name_to_id_mapper_sub['created_at']]
            except:
                created_at = ''
            # collect all subject data
            subject_data_all = {
                'subject_id': subject_id,
                'retired_at': retired_at,
                'retirement_reason': retirement_reason,
                'created_at': created_at,
                **locations_dict,
                **metadata_dict
            }
            # gather all subject info to add
            subject_info_to_add = OrderedDict()
            # add subject_id per default
            subject_info_to_add['subject_id'] = subject_id
            # add location data if specified
            if flags['SUBJECT_ADD_LOCATION_DATA']:
                for location_key in locations_dict.keys():
                    subject_info_to_add[location_key] = \
                        subject_data_all[location_key]
            # add the specified meta-data
            for field in flags['SUBJECT_METADATA_TO_ADD']:
                try:
                    subject_info_to_add[field] = subject_data_all[field]
                except:
                    subject_info_to_add[field] = ''
            for field in flags['SUBJECT_DATA_TO_ADD']:
                try:
                    subject_info_to_add[field] = subject_data_all[field]
                except:
                    subject_info_to_add[field] = ''
            subject_info_to_add = extractor.rename_dict_keys(
                subject_info_to_add, flags['SUBJECT_DATA_NAME_MAPPER'])
            subject_info[subject_id] = subject_info_to_add

    # Export Data as CSV
    df_out = pd.DataFrame.from_dict(subject_info, orient='index')

    # order columns
    df_out_cols = list(df_out.columns)
    df_out_cols.sort()
    first_cols_if_available = [
        'subject_id', 'capture_id', 'season', 'site', 'roll', 'capture']
    first_cols = [x for x in first_cols_if_available if x in df_out_cols]
    last_cols = [x for x in df_out_cols if x not in first_cols]
    cols_ordered = first_cols + last_cols
    df_out = df_out[cols_ordered]

    df_out.fillna('', inplace=True)

    logger.info("Writing output to {}".format(args['output_csv']))

    df_out.to_csv(args['output_csv'], index=False)

    logger.info("Wrote {} records to {}".format(
        df_out.shape[0], args['output_csv']))

    # change permmissions to read/write for group
    set_file_permission(args['output_csv'])
