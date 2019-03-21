""" Create Reports Based on Zooniverse Data """
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
flags_global = cfg['global_processing_flags']
flags_report = cfg['report_flags']

# args = dict()
# args['season_captures_csv'] = '/home/packerc/shared/season_captures/GRU/cleaned/GRU_S1_cleaned.csv'
# args['aggregated_csv'] = '/home/packerc/shared/zooniverse/Aggregations/GRU/GRU_S1_annotations_aggregated_subject_info.csv'
# args['output_csv'] = '/home/packerc/shared/zooniverse/ConsensusReports/GRU/GRU_S1_report_all.csv'
# args['log_dir'] = '/home/packerc/shared/zooniverse/ConsensusReports/GRU/'
# args['default_season_id'] = 'GRU_S1'
# args['deduplicate_subjects'] = True
# args['export_only_species'] = False
# args['export_only_with_aggregations'] = True


def deduplicate_captures(df_aggregated):
    """ De-Duplicate Captures with multiple subjects """
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
    return df_aggregated


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
    parser.add_argument("--exclude_non_consensus", action="store_true")
    parser.add_argument("--exclude_humans", action="store_true")
    parser.add_argument("--exclude_blanks", action="store_true")
    parser.add_argument("--exclude_captures_without_data", action="store_true")
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

    # determine empty/blank answer
    question_main_id = flags_global['QUESTION_DELIMITER'].join(
        [flags_global['QUESTION_PREFIX'], flags_global['QUESTION_MAIN']])
    question_column_prefix = '{}{}'.format(
        flags_global['QUESTION_PREFIX'],
        flags_global['QUESTION_DELIMITER'])

    # create stats variables
    n_humans_excluded = 0
    n_blanks_excluded = 0
    n_non_consensus_excluded = 0
    n_without_data_excluded = 0

    ###############################
    # Read / Process Aggregations
    ###############################

    # import aggregations
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
    df_aggregated = deduplicate_captures(df_aggregated)

    # Store aggregated data per capture
    aggregated_data = dict()
    header_input = df_aggregated.columns
    for line_no, line in df_aggregated.iterrows():
        capture_id = line['capture_id']
        main_answer = line[question_main_id]
        # Skip non-consensus aggregations if specified
        if args['exclude_non_consensus']:
            try:
                if line['species_is_plurality_consensus'] == '0':
                    n_non_consensus_excluded += 1
                    continue
            except:
                pass
        # Exclude humans
        if args['exclude_humans']:
            if main_answer in flags_report['humans']:
                logger.debug("Exclude capture {} because of human".format(
                    capture_id))
                n_humans_excluded += 1
                continue
        # Exclude blanks
        if args['exclude_blanks']:
            if main_answer == flags['QUESTION_MAIN_EMPTY']:
                logger.debug("Exclude capture {} because it is blank".format(
                    capture_id))
                n_blanks_excluded += 1
                continue
        try:
            aggregated_data[capture_id].append(line)
        except:
            aggregated_data[capture_id] = [line]

    ###############################
    # Read Captures Data
    ###############################

    # read captures data
    season_data_df = read_cleaned_season_file_df(args['season_captures_csv'])

    # Create per Capture Data
    season_dict = create_season_dict(season_data_df)

    # get the season data columns from a random record
    random_record = season_dict[list(season_dict.keys())[0]]
    season_header = list(random_record.keys())

    ###############################
    # Create Reports
    ###############################

    # Create Report Dict
    report_list = list()
    agg_data_to_add = [x for x in header_input if x not in season_header]

    for line_no, (capture_id, season_data) in enumerate(season_dict.items()):
        # skip captures without aggregations if specified
        capture_has_aggregations = (capture_id in aggregated_data)
        if args['exclude_captures_without_data']:
            if not capture_has_aggregations:
                n_without_data_excluded += 1
                continue
        # for each capture get all annotations
        aggregations_list = aggregated_data[capture_id]
        for aggregation in aggregations_list:
            row = list()
            row += [season_data[x] for x in season_header]
            row += [aggregation[x] for x in agg_data_to_add]
            report_list.append(row)

    # report stats
    logger.info("Excluded {} blank aggregations".format(n_blanks_excluded))
    logger.info("Excluded {} human aggregations".format(n_humans_excluded))
    logger.info("Excluded {} non-consensus aggregations".format(
        n_non_consensus_excluded))
    logger.info("Excluded {} without aggregations".format(
        n_without_data_excluded))

    # build df
    df_report = pd.DataFrame(report_list)
    df_report.columns = season_header + agg_data_to_add

    # export df
    df_report.to_csv(args['output_csv'], index=False)

    logger.info("Wrote {} records to {}".format(
        df_report.shape[0], args['output_csv']))

    # change permmissions to read/write for group
    set_file_permission(args['output_csv'])
