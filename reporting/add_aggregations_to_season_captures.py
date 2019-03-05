""" Add Zooniverse Aggregations to Season Captures """
import csv
import logging
import os
import argparse
import textwrap
import pandas as pd
from datetime import datetime
from collections import OrderedDict

from logger import setup_logger, create_log_file
from utils import read_cleaned_season_file, set_file_permission
from global_vars import plurality_aggregation_flags as flags

# args = dict()
# args['season_captures_csv'] = '/home/packerc/shared/season_captures/GRU/cleaned/GRU_S1_cleaned.csv'
# args['aggregated_csv'] = '/home/packerc/shared/zooniverse/Exports/GRU/GRU_S1_classifications_aggregated_samples_subject_info.csv'
# args['output_csv'] = '/home/packerc/shared/zooniverse/Exports/GRU/GRU_S1_report.csv'
# args['default_season_id'] = 'GRU_S1'
# args['deduplicate_subjects'] = True
# args['export_only_species'] = False
# args['export_only_with_aggregations'] = True

if __name__ == '__main__':

    # Parse command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("--season_captures_csv", type=str, required=True)
    parser.add_argument("--aggregated_csv", type=str, required=True)
    parser.add_argument("--output_csv", type=str, required=True)
    parser.add_argument("--default_season_id", type=str, default='')
    parser.add_argument("--export_only_with_aggregations", action="store_true")
    parser.add_argument("--export_only_species", action="store_true")
    parser.add_argument("--deduplicate_subjects", action="store_true")
    parser.add_argument(
        "--log_dir", type=str, default=None)
    parser.add_argument(
        "--log_filename", type=str,
        default='add_aggregations_to_season_captures')

    args = vars(parser.parse_args())

    ######################################
    # Check Input
    ######################################

    if not os.path.isfile(args['season_captures_csv']):
        raise FileNotFoundError("season_captures_csv: {} not found".format(
                                args['season_captures_csv']))

    if not os.path.isfile(args['aggregated_csv']):
        raise FileNotFoundError("aggregated_csv: {} not found".format(
                                args['aggregated_csv']))

    # logging
    if args['log_dir'] is not None:
        log_file_path = create_log_file(args['log_dir'], args['log_filename'])
        setup_logger(log_file_path)
    else:
        setup_logger()
    logger = logging.getLogger(__name__)

    season_data, header = read_cleaned_season_file(args['season_captures_csv'])

    # determine empty/blank answer
    question_main_id = flags['QUESTION_DELIMITER'].join(
        [flags['QUESTION_PREFIX'], flags['QUESTION_MAIN']])
    question_column_prefix = '{}{}'.format(
        flags['QUESTION_PREFIX'],
        flags['QUESTION_DELIMITER'])

    # Create per Capture Data
    season_dict = OrderedDict()
    for image_record in season_data:
        if 'capture_id' not in header:
            capture_id = '#'.join([
                image_record[header['season']],
                image_record[header['site']],
                image_record[header['roll']],
                image_record[header['capture']],
            ])
        else:
            capture_id = image_record[header['capture_id']]
        if capture_id not in season_dict:
            timestamp = image_record[header['timestamp']]
            # deal with different timeformats in different capture files
            try:
                time_obj = datetime.strptime(timestamp, '%Y:%m:%d %H:%M:%S')
            except ValueError:
                try:
                    time_obj = datetime.strptime(
                        timestamp,
                        '%Y-%m-%d %H:%M:%S')
                except ValueError:
                    time_obj = datetime.strptime(
                        timestamp,
                        '%Y-%m-%d %H:%M:%SZ')
            date = time_obj.strftime("%Y-%m-%d")
            time = time_obj.strftime("%H:%M:%S")
            season_dict[capture_id] = {
                'capture_id': capture_id,
                'season': image_record[header['season']],
                'site': image_record[header['site']],
                'roll': image_record[header['roll']],
                'capture': image_record[header['capture']],
                'capture_date_local': date,
                'capture_time_local': time}

    season_header = list(season_dict[capture_id].keys())

    # read aggregations
    df_aggregated = pd.read_csv(args['aggregated_csv'], dtype='str')
    df_aggregated.fillna('', inplace=True)
    df_aggregated.loc[df_aggregated.season == '', 'season'] = \
        args['default_season_id']

    # add capture id if not specified
    if 'capture_id' not in df_aggregated.columns:
        for _id, row in df_aggregated.iterrows():
            capture_id = '#'.join(
                [row.season, row.site, row.roll, row.capture])
            df_aggregated.loc[_id, 'capture_id'] = capture_id

    # deduplicate Aggregated data
    if args['deduplicate_subjects']:
        capture_to_subject_mapping = dict()
        duplicate_subject_ids = set()
        for row_id, row_data in df_aggregated.iterrows():
            capture_id = row_data['capture_id']
            subject_id = row_data['subject_id']
            if capture_id not in capture_to_subject_mapping:
                capture_to_subject_mapping[capture_id] = subject_id
                continue
            else:
                known_subject_id = capture_to_subject_mapping[capture_id]
                is_identical = (known_subject_id == subject_id)
            if not is_identical:
                msg = textwrap.shorten(
                    "Subject_ids with identical capture_id found -- \
                     capture_id {} - subject_ids {} - {}".format(
                     capture_id, known_subject_id, subject_id
                     ), width=99)
                logger.warning(msg)
            duplicate_subject_ids.add(subject_id)
        logger.info("Found {} subjects with identical capture ids".format(
            len(duplicate_subject_ids)))
        if len(duplicate_subject_ids) > 0:
            df_aggregated = \
                df_aggregated[~df_aggregated['subject_id'].isin(
                    duplicate_subject_ids)]

    # Store all info per capture
    aggregated_data = dict()
    header_input = df_aggregated.columns
    row_name_to_id_mapper_input = {x: i for i, x in enumerate(header_input)}
    for line_no, line in df_aggregated.iterrows():
        capture_id = line['capture_id']
        if capture_id not in aggregated_data:
            aggregated_data[capture_id] = list()
        aggregated_data[capture_id].append(line)

    agg_data_header = [x for x in header_input if x not in season_header]
    header_combined = season_header + agg_data_header

    # Write Season File with Aggregations
    with open(args['output_csv'], 'w') as f:
        csv_writer = csv.writer(f, delimiter=',')
        logger.info("Writing output to {}".format(args['output_csv']))
        csv_writer.writerow(header_combined)
        n_lines_written = 0
        n_lines_with_aggregations = 0
        for line_no, (capture_id, season_data) in enumerate(season_dict.items()):
            # get subject info data
            season_info_to_write = list()
            for x in season_header:
                try:
                    season_info_to_write.append(season_data[x])
                except:
                    season_info_to_write.append('')
            capture_has_answers = (capture_id in aggregated_data)
            export_captures_without_answers = (
                args['export_only_species'] or
                args['export_only_with_aggregations'])
            if capture_has_answers:
                # write one line for each aggregation
                for agg_data_dict in aggregated_data[capture_id]:
                    to_write = list()
                    for x in agg_data_header:
                        try:
                            to_write.append(agg_data_dict[x])
                        except:
                            to_write.append('')
                    if args['export_only_species']:
                        main_answer = agg_data_dict[question_main_id]
                        if main_answer == flags['QUESTION_MAIN_EMPTY']:
                            continue
                    csv_writer.writerow(season_info_to_write + to_write)
                    n_lines_written += 1
                    n_lines_with_aggregations += 1
            elif not export_captures_without_answers:
                to_write = ['' for i in range(0, len(agg_data_header))]
                csv_writer.writerow(season_info_to_write + to_write)
                n_lines_written += 1
            # print status
            if ((line_no % 10000) == 0) and (line_no > 0):
                print("Processed {:,} captures".format(line_no))
        logger.info("Wrote {} records to {}".format(
            n_lines_written, args['output_csv']))
        logger.info("Wrote {} records with aggregations to {}".format(
            n_lines_with_aggregations, args['output_csv']))

    # change permmissions to read/write for group
    set_file_permission(args['output_csv'])
