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
from utils import set_file_permission, read_cleaned_season_file_df
from config.cfg import cfg


flags = cfg['plurality_aggregation_flags']

# args = dict()
# args['season_captures_csv'] = '/home/packerc/shared/season_captures/GRU/cleaned/GRU_S1_cleaned.csv'
# args['aggregated_csv'] = '/home/packerc/shared/zooniverse/Aggregations/GRU/GRU_S1_annotations_aggregated_subject_info.csv'
# args['output_csv'] = '/home/packerc/shared/zooniverse/ConsensusReports/GRU/GRU_S1_report_all.csv'
# args['log_dir'] = '/home/packerc/shared/zooniverse/ConsensusReports/GRU/'
# args['default_season_id'] = 'GRU_S1'
# args['deduplicate_subjects'] = True
# args['export_only_species'] = False
# args['export_only_with_aggregations'] = True


def create_season_dict(season_data_df):
    """ Create Dict of Season Data """
    season_dict = OrderedDict()
    season_dict_input = season_data_df.to_dict(orient='index')
    for _id, image_record in season_dict_input.items():
        try:
            capture_id = image_record['capture_id']
        except:
            capture_id = '#'.join([
                image_record['season'],
                image_record['site'],
                image_record['roll'],
                image_record['capture']])
        if capture_id not in season_dict:
            timestamp = image_record['timestamp']
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
                'season': image_record['season'],
                'site': image_record['site'],
                'roll': image_record['roll'],
                'capture': image_record['capture'],
                'capture_date_local': date,
                'capture_time_local': time}
    return season_dict


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
    parser.add_argument("--export_only_consensus", action="store_true")
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

    season_data_df = read_cleaned_season_file_df(args['season_captures_csv'])

    # determine empty/blank answer
    question_main_id = flags['QUESTION_DELIMITER'].join(
        [flags['QUESTION_PREFIX'], flags['QUESTION_MAIN']])
    question_column_prefix = '{}{}'.format(
        flags['QUESTION_PREFIX'],
        flags['QUESTION_DELIMITER'])

    # Create per Capture Data
    season_dict = create_season_dict(season_data_df)

    random_record = season_dict[list(season_dict.keys())[0]]
    season_header = list(random_record.keys())

    # read aggregations
    df_aggregated = pd.read_csv(args['aggregated_csv'], dtype='str')
    df_aggregated.fillna('', inplace=True)
    df_aggregated.loc[df_aggregated.season == '', 'season'] = \
        args['default_season_id']

    # add capture id if not specified
    if 'capture_id' not in df_aggregated.columns:
        capture_ids_all = list()
        for _id, row in df_aggregated.iterrows():
            capture_id = '#'.join(
                [row.season, row.site, row.roll, row.capture])
            capture_ids_all.append(capture_id)
        df_aggregated['capture_id'] = capture_ids_all

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
                     ), width=150)
                logger.warning(msg)
                duplicate_subject_ids.add(subject_id)
        msg = textwrap.shorten(
                "Found {} subjects that have identical capture id to other \
                 subjects - removing them ...".format(
                 len(duplicate_subject_ids)), width=150)
        logger.warning(msg)
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
        # Skip plurality consensus species
        if args['export_only_consensus']:
            try:
                if line['species_is_plurality_consensus']:
                    continue
            except:
                pass
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
