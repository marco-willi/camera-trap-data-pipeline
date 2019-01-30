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
    - Season WTF example (messed up - no capture_id):
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
import time
import os
from collections import Counter

from zooniverse_exports import legacy_extractor


######################################
# Parameters
######################################

args = dict()
args['classification_csv'] = '/home/packerc/shared/zooniverse/Exports/SER/2019-01-27_serengeti_classifications.csv'
args['output_csv'] = '/home/packerc/shared/zooniverse/Exports/SER/SER_S1_S10_classifications_extracted.csv'
args['output_path'] = '/home/packerc/shared/zooniverse/Exports/SER/'
args['season_captures_path'] = '/home/packerc/shared/season_captures/SER/captures/'
args['split_raw_file'] = False
all_seasons_ids = [
    'S1', 'S2', 'S3', 'S4', 'S5', 'S6',
    'S7', 'S8', 'S9', '10', 'WF1', 'tutorial']

######################################
# Configuration
######################################

flags = dict()

# map column names of the input csv for clarity and consistency
flags['CSV_HEADER_MAPPER'] = {
    'id': 'classification_id',
    'subject_zooniverse_id': 'subject_id',
    "species_count": 'count',
    "babies": 'young_present'
    }

# map different answers to the question columns
flags['ANSWER_TYPE_MAPPER'] = {
    'species': {
        'no animals present': 'blank',
        'nothing': 'blank',
        '': 'blank'
        },
    'young_present': {
        'false': 0,
        'true': 1
        },
    'standing': {
        'false': 0,
        'true': 1
        },
    'resting': {
        'false': 0,
        'true': 1
        },
    'moving': {
        'false': 0,
        'true': 1
        },
    'eating': {
        'false': 0,
        'true': 1
        },
    'interacting': {
        'false': 0,
        'true': 1
        }
    }

# Define the question columns
flags['CSV_QUESTIIONS'] = [
    'species', 'count', 'young_present',
    "standing", "resting", "moving", "eating", "interacting"]

# Columns to export
flags['CLASSIFICATION_INFO_TO_ADD'] = [
    'user_name', 'created_at', 'subject_id', 'capture_event_id',
    "retire_reason", "season", "site", "roll", "filenames", "timestamps",
    'classification_id']

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


s_id = 'S1'

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
    legacy_extractor.consolidate_all_classifications(classifications)

# merge consolidated annotations into classifications dict
for c_id, annotations in consolidated_classifications.items():
    classifications[c_id] = annotations

######################################
# Print Stats
######################################

retire_reasons = list()
seasons = list()
answers = {k: list() for k in flags['CSV_QUESTIIONS']}

for c_id, annotations in classifications.items():
    if not isinstance(annotations, list):
        print(annotations)
        time.sleep(3)
    for annotation in annotations:
        retire_reasons.append(annotation['retire_reason'])
        seasons.append(annotation['season'])
        for question, _answers_list in answers.items():
            _answers_list.append(annotation[question])

season_stats = Counter(seasons)
retire_reasons_stats = Counter(retire_reasons)
answers_stats = {k: Counter(v).most_common() for k, v in answers.items()}
season_stats.most_common()
retire_reasons_stats.most_common()

for stat in answers_stats:
    for question, n in stat.items():
        print('{:10}:{}'.formate(question, n))

# Print examples
for i, (_id, data) in enumerate(classifications.items()):
    if i > 10:
        break
    print("ID: {}, Data: {}".format(_id, data))


######################################
# Export File
######################################

args['output_csv']
def export_cleaned_annotations(path, classifications):
    """ Export Cleaned Annotation """
    with open(path, 'w') as f:
        csv_writer = csv.writer(f, delimiter=',')
        print("Writing output to %s" % path)
        csv_writer.writerow(header)
        tot = len(all_records)
        for line_no, (_c_id, data) in classifications.items():

        for line_no, record in enumerate(all_records):
            # get classification info data
            class_data = [record[x] for x in CLASSIFICATION_INFO_TO_ADD]
            # get annotation info data
            answers = unpack_annotations(record['annos'])
            answers_ordered = [answers[x] if x in answers else '' for x in questions]
            csv_writer.writerow(class_data + answers_ordered)
            print_progress(line_no, tot)
