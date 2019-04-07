""" Code to extract legacy Zooniverse classification
    exports from Serengeti S1-S10

    - input is a Zooniverse classification export (Oruboros export)
    - output are extracted classifications in the same format as
      newer SnapshotSafari data
    - base code:
        https://github.com/mkosmala/SnapshotSerengetiScripts/
        - re-implemented due to consistency and efficiency resons
    - raw data header:
        "id","user_name","subject_zooniverse_id","capture_event_id",
        "created_at","retire_reason","season","site","roll","filenames",
        "timestamps","species","species_count","standing","resting","moving",
        "eating","interacting","babies"
    - data record example:
        "50c6724f56175a1f4f000490","brian-c","ASG000b3r2","tutorial",
        "2012-12-10 23:37:51 UTC","none","tutorial","tutorial","tutorial",
        "tutorial","tutorial","wildebeest","1","false","false","true",
        "false","false","false"
    - Code-Structure:
        - read csv file
        - map column names
        - check and combine classifications if required
        - export
    - MSI-Processing
        - qsub -I -l walltime=18:00:00,nodes=1:ppn=8,mem=32gb
    - Season 10 example (messed up - no capture_id, some with retirement):
        "5a789769b941903402000716","travelling_louise","ASG001xfu1","tutorial",
        "2018-02-05 17:42:01 UTC","consensus","10","H04","2",
        "S10_H04_R2_IMAG0251.JPG;S10_H04_R2_IMAG0252.JPG;S10_H04_R2_IMAG0253.JPG",
        "2015-04-19 15:46:26;2015-04-19 15:46:26;2015-04-19 15:46:26",
        "cattle","8","false","true","false","false","false","false"
        ['58f78349933b5d0074000338',
         'not-logged-in-efe6890d709f658e6f6e494e2fed3f27', 'ASG001ttdo',
         'tutorial', '2017-04-19 15:33:29 UTC', 'none', '10', 'J12', '1',
         'S10_J12_R1_IMAG0619.JPG;S10_J12_R1_IMAG0620.JPG;S10_J12_R1_IMAG0621.JPG',
         '2015-02-17 12:53:29;2015-02-17 12:53:29;2015-02-17 12:53:29',
         'guineaFowl', '2', 'true', 'false', 'false', 'false',
         'false', 'false'],
         ['58f79dcb933b5d00890004ec', 'LoisH', 'ASG001w7le', 'tutorial',
          '2017-04-19 17:26:35 UTC', 'blank', '10', 'Q07', '1',
          'S10_Q07_R1_IMAG1016.JPG;S10_Q07_R1_IMAG1017.JPG;S10_Q07_R1_IMAG1018.JPG',
          '2015-02-10 17:53:47;2015-02-10 17:53:47;2015-02-10 17:53:47',
          '', '', '', '', '', '', '', '']
    - Season WF1 example (messed up - no capture_id):
        ['578909a76053a9532d00052f', 'maricksu', 'ASG001qto9', 'tutorial',
         '2016-07-15 16:04:55 UTC', 'none', 'WF1', 'SIM', '13',
         'WF1_SIM_R13_EK001358.JPG', '2014-12-16 10:06:00',
         'wildebeest', '7', 'false', 'false', 'false', 'true', 'false',
         'false'],
        ['57890aa26053a9165800001f', 'maricksu', 'ASG001se9e', 'tutorial',
         '2016-07-15 16:09:06 UTC', 'none', 'WF1', 'SOT', '5',
         'WF1_SOT_R5_EK000150.JPG', '2013-11-06 02:50:00',
          '', '', '', '', '', '', '', '']
    - Season S9 example (messed up - no capture_id):
        ['56b20a50f724d71f2b000c47', 'n68570', 'ASG001h3lb',
         'tutorial', '2016-02-03 14:10:24 UTC', 'none', 'S9', 'E12', '2',
         'S9_E12_R2_IMAG0388.JPG;S9_E12_R2_IMAG0389.JPG;S9_E12_R2_IMAG0390.JPG',
         '2014-08-20 10:46:42;2014-08-20 10:46:42;2014-08-20 10:46:42',
         '', '', '', '', '', '', '', ''],
        ['56b20941f724d71579000b7c', 'UncleIan', 'ASG001oal6', 'tutorial',
         '2016-02-03 14:05:53 UTC', 'none', 'S9', 'C13', '1',
         'S9_C13_R1_IMAG1034.JPG;S9_C13_R1_IMAG1035.JPG;S9_C13_R1_IMAG1036.JPG',
         '2014-08-07 16:21:51;2014-08-07 16:21:51;2014-08-07 16:21:51',
         'elephant', '3', 'true', 'false', 'false', 'false', 'false', 'false']
    - Notes:
        /home/packerc/shared/season_captures/SER/captures
        Season, Site, Roll, Capture, Image, PathFilename, TimestampJPG
        1,B04,1,1,1,S1/B04/B04_R1/PICT0001.JPG,2010:07:18 16:26:14

        /home/packerc/shared/time_stamp_cleaning/CleanedCaptures/SER
        "season","site","roll","capture","image","path","newtime","oldtime","invalid","include"
        10,"B03",1,1,1,"S10/B03/B03_R1/S10_B03_R1_IMAG0001.JPG","2015-01-16 11:31:41","2015:01:16 11:31:41",0,1
        10,"B03",1,1,2,"S10/B03/B03_R1/S10_B03_R1_IMAG0002.JPG","2015-01-16 11:31:43","2015:01:16 11:31:43",0,1

        /home/packerc/shared/metadata_db/data/link_to_zoon_id/old
        idCaptureEvent,ZoonID
        86127,ASG0001aac
        86127,ASG0001aad
        128298,ASG000206d
        128484,ASG00020es
        62105,ASG0002bu5
        479233,ASG0008i2e

        /home/packerc/shared/season_captures/SER/captures
        S1 is incomplete, for one site the image numbers go to 4k in the captures.csv but on
        disk and on Zooniverse there are 5k images
        also not found this in the SerengetiDB: grep V13_R1/PICT6148.JPG
"""
import os
import argparse
from collections import Counter
import logging
from logger import setup_logger, create_log_file

from zooniverse_exports import legacy_extractor
from utils import print_nested_dict, set_file_permission
from config.cfg import cfg


flags = cfg['legacy_extractor_flags']

# To Test
# args = dict()
# args['classification_csv'] = '/home/packerc/shared/zooniverse/Exports/SER/2019-01-27_serengeti_classifications.csv'
# args['output_path'] = '/home/packerc/shared/zooniverse/Exports/SER/'
# args['season_captures_path'] = '/home/packerc/shared/season_captures/SER/captures/'
# args['season_to_process'] = 'S2'
# args['split_raw_file'] = False

# python3 -m zooniverse_exports.extract_legacy_serengeti \
# --classification_csv '/home/packerc/shared/zooniverse/Exports/SER/2019-01-27_serengeti_classifications.csv' \
# --output_path '/home/packerc/shared/zooniverse/Exports/SER/' \
# --season_to_process 'S1'

######################################
# Parameters
######################################

if __name__ == '__main__':

    # Parse command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--classification_csv", type=str, required=True,
        help="classifications csv")
    parser.add_argument(
        "--output_path", type=str, required=True,
        help="Output path for csv results")
    parser.add_argument(
        '--season_to_process', type=str, required=True)
    parser.add_argument(
        '--season_captures_path', type=str,
        default='/home/packerc/shared/season_captures/SER/captures/',
        help="Path to dir with captures.csvs")
    parser.add_argument(
        '--split_raw_file', action='store_true',
        help="Split the raw file according to seasons. If not specified, the \
              script assumes those files exist already.")
    parser.add_argument(
        "--log_dir", type=str, default=None)
    parser.add_argument(
        "--log_filename", type=str,
        default='extract_legacy_serengeti')

    args = vars(parser.parse_args())
    s_id = args['season_to_process']

    all_seasons_ids = [
        'S1', 'S2', 'S3', 'S4', 'S5', 'S6',
        'S7', 'S8', 'S9', '10', 'WF1', 'tutorial']

    if args['season_to_process'] not in all_seasons_ids:
        raise ValueError("season_to_process must be one of {}".format(
            all_seasons_ids))

    if not os.path.isdir(args['output_path']):
        raise ValueError("output_path: {} must be a directory".format(
            args['output_path']))

    if not os.path.isfile(args['classification_csv']):
        raise ValueError("classification_csv: {} must be a file".format(
            args['classification_csv']))

    ######################################
    # Configuration
    ######################################

    # logging
    if args['log_dir'] is not None:
        log_file_path = create_log_file(args['log_dir'], args['log_filename'])
        setup_logger(log_file_path)
    else:
        setup_logger()
    logger = logging.getLogger(__name__)

    for k, v in args.items():
        logger.info("Argument {}: {}".format(k, v))

    # logging flags
    print_nested_dict('', flags)

    ######################################
    # Split the complete Zooniverse export
    # into season files
    # - SER_{}_classifications_raw.csv
    ######################################

    if args['split_raw_file']:
        file_writers = legacy_extractor.split_raw_classification_csv(
            args['classification_csv'], args['output_path'])
        all_seasons = {
            k: os.path.join(
                args['output_path'],
                'SER_{}_classifications_raw.csv'.format(k))
            for k in file_writers.keys()}
    else:
        # create the season file paths
        all_seasons = {
            k: os.path.join(
                args['output_path'],
                'SER_{}_classifications_raw.csv'.format(k))
            for k in all_seasons_ids}

    for season, season_path in all_seasons.items():
        logger.info("Season: {} classifications stored at: {}".format(
            season, season_path))

    ######################################
    # Read meta-data from season capture
    # files
    ######################################

    season_capture_files = dict()
    for k, v in all_seasons.items():
        season_capture_files[k] = os.path.join(
            args['season_captures_path'],
            '{}_captures.csv'.format(k))

    # special fix for S10
    season_capture_files['10'] = os.path.join(
        args['season_captures_path'],
        '{}_captures.csv'.format('S10'))

    for season, season_path in season_capture_files.items():
        logger.info("Season: {} meta-data defined to be at: {}".format(
            season, season_path))

    img_to_capture = legacy_extractor.build_img_to_capture_map(
        season_capture_files[s_id], flags)

    ######################################
    # Process Classifications
    ######################################

    season_file = all_seasons[s_id]

    classifications = legacy_extractor.process_season_classifications(
        season_file, img_to_capture, flags)

    ######################################
    # Consolidate Classifications with
    # multiple entries of the same
    # species
    ######################################

    consolidated_classifications = \
        legacy_extractor.consolidate_all_classifications(
            classifications, flags)

    # merge consolidated annotations into classifications dict
    for c_id, annotations in consolidated_classifications.items():
        classifications[c_id] = annotations

    ######################################
    # Print Stats
    ######################################

    retirement_reasons = list()
    seasons = list()
    answers = {k: list() for k in flags['CSV_QUESTIONS']}

    try:
        retirement_reason = flags['CSV_HEADER_MAPPER']['retire_reason']
    except:
        retirement_reason = 'retire_reason'

    for c_id, annotations in classifications.items():
        if not isinstance(annotations, list):
            logger.info(annotations)
        for annotation in annotations:
            retirement_reasons.append(annotation[retirement_reason])
            seasons.append(annotation['season'])
            for question, _answers_list in answers.items():
                _answers_list.append(annotation[question])

    season_stats = Counter(seasons)
    retirement_reasons_stats = Counter(retirement_reasons)
    answers_stats = {k: Counter(v).most_common() for k, v in answers.items()}
    season_stats.most_common()
    retirement_reasons_stats.most_common()

    for question, question_stats in answers_stats.items():
        logger.info("Stats for question: %s" % question)
        n_tot = sum([x[1] for x in question_stats])
        for (answer, n) in question_stats:
            percent = (n / n_tot) * 100
            logger.info('{:15} - {:15} - {:10} / {} ({:.2f} %)'.format(
                question, answer, n, n_tot, percent))

    # Print examples
    logger.info("Show some example classifications")
    for i, (_id, data) in enumerate(classifications.items()):
        if i > 10:
            break
        logger.info("ID: {}, Data: {}".format(_id, data))

    ######################################
    # Export Annotations to a File
    ######################################

    # access a random classification and get all the keys of the first
    # annotation -- this is consistent for all other annotations
    header = list(classifications[list(classifications.keys())[0]][0].keys())

    output_paths = {
        k: os.path.join(
            args['output_path'],
            'SER_{}_annotations.csv'.format(k))
        for k in all_seasons.keys()}

    legacy_extractor.export_cleaned_annotations(
        output_paths[s_id], classifications, header, flags)

    # change permmissions to read/write for group
    set_file_permission(output_paths[s_id])
