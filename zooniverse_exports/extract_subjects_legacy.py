""" Generate an extracted subjects.csv based on the classifications
    Output:
        capture,created_at,retired_at,retirement_reason,roll,season,
        site,subject_id,zooniverse_url_0,zooniverse_url_1,zooniverse_url_2
"""
import os
import pandas as pd
import csv
import logging
import argparse
from collections import OrderedDict

from logger import setup_logger, create_logfile_name
from utils import set_file_permission
from zooniverse_exports.legacy_extractor import build_img_path

from global_vars import add_subject_info_flags_legacy as flags

# args = dict()
# args['classifications_extracted'] = '/home/packerc/shared/zooniverse/Exports/SER/SER_S1_classifications_extracted.csv'
# args['output_csv'] = '/home/packerc/shared/zooniverse/Exports/SER/SER_S1_subjects_extracted.csv'

if __name__ == '__main__':

    # Parse command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("--classifications_extracted", type=str, required=True)
    parser.add_argument("--output_csv", type=str, required=True)

    args = vars(parser.parse_args())

    ######################################
    # Check Input
    ######################################

    if not os.path.isfile(args['classifications_extracted']):
        raise FileNotFoundError(
            "classifications_extracted: {} not found".format(
             args['classifications_extracted']))

    flags.sort()

    # logging
    log_file_name = create_logfile_name('extract_subjects_legacy')
    log_file_path = os.path.join(
        os.path.dirname(args['output_csv']), log_file_name)
    setup_logger(log_file_path)
    logger = logging.getLogger(__name__)

    ######################################
    # Read Classifications
    ######################################

    # Read Subject CSV
    class_dict = OrderedDict()
    with open(args['classifications_extracted'], "r") as ins:
        csv_reader = csv.reader(ins, delimiter=',', quotechar='"')
        header = next(csv_reader)
        row_name_to_id_mapper = {x: i for i, x in enumerate(header)}
        for line_no, line in enumerate(csv_reader):
            subject_id = line[row_name_to_id_mapper['subject_id']]
            record = {k: line[v] for k, v in row_name_to_id_mapper.items()}
            class_dict[subject_id] = record

    ######################################
    # Create subject data
    ######################################

    # Create one row per subject
    subjects = OrderedDict()
    for cl in class_dict.values():
        subject_id = cl['subject_id']
        record = dict()
        for flag in flags:
            try:
                record[flag] = cl[flag]
            except:
                record[flag] = ''
            # correct image paths
            if "filenames" in record:
                try:
                    filenames = record['filenames'].split(';')
                    roll = record['roll']
                    season = record['season']
                    site = record['site']
                    filenames = [
                        build_img_path(season, site, roll, x)
                        for x in filenames]
                    record['filenames'] = ';'.join(filenames)
                except:
                    pass

        record['subject_id'] = subject_id
        subjects[subject_id] = record

    ######################################
    # Export as CSV
    ######################################

    df = pd.DataFrame.from_dict(subjects, orient='index')

    # sort rows
    df.sort_values(
        by=['season', 'site', 'roll', 'capture', 'subject_id'], inplace=True)

    # export
    df.to_csv(args['output_csv'], index=False)

    # change permmissions to read/write for group
    set_file_permission(args['output_csv'])
