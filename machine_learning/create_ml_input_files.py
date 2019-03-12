""" Create Machine Learning Inventory files -
    These files can be used to create TFRecords from
"""
import pandas as pd
import os
from collections import Counter

from config.cfg import ml_mappings
from utils import (
    set_file_permission, sort_df_by_capture_id,
    id_to_zero_one, assign_zero_one_to_split)
from machine_learning.utils import find_all_reports


root_path = '/home/packerc/shared/zooniverse/ConsensusReports/'
output_root_path = '/home/packerc/shared/machine_learning/data/info_files/'
reports = find_all_reports(root_path, report_postfix='_report.csv')

species_mapping = ml_mappings['species_mappings']
species_mapping = {k.lower(): v for k, v in species_mapping.items()}
questions = ml_mappings['questions_to_output']
question_types = ml_mappings['question_types']
behavior_labels = ml_mappings['question_behaviors']
split_percent = [0.9, 0.05, 0.05]
split_names = ['train', 'val', 'test']

question_prefix = 'question__'
questions_pfx = ['{}{}'.format(question_prefix, x) for x in questions]
behavior_labels_pfx = ['{}{}'.format(question_prefix, x) for x in behavior_labels]

output_header = [
    'capture_id', 'subject_id', 'season', 'site', 'roll',
    'capture', 'capture_date_local', 'capture_time_local']


def convert_answer(data, type):
    if type == 'cat':
        return data
    if type == 'binary':
        try:
            return str(int(float(data) + 0.5))
        except:
            return '0'


def set_max_binary_to_one(row):
    max_val = max(row.values())
    if max_val == '':
        return row
    if float(max_val) < 0.25:
        return row
    mapped = dict()
    for k, v in row.items():
        if v == max_val:
            mapped[k] = '1'
        else:
            mapped[k] = v
    return mapped


def create_ml_file_all(path_report, path_cleaned, path_output):
    df_report = pd.read_csv(path_report, dtype='str', index_col=None)
    df_report.fillna('', inplace=True)
    df_report_list = df_report.to_dict(orient='records')
    df_cleaned = pd.read_csv(path_cleaned, dtype='str', index_col=None)
    df_cleaned.fillna('', inplace=True)
    df_cleaned_list = df_cleaned.to_dict(orient='records')
    # generate capture id if not present
    if 'capture_id' not in df_cleaned.columns:
        for df_cleaned_record in df_cleaned_list:
            season = df_cleaned_record['season']
            site = df_cleaned_record['site']
            roll = df_cleaned_record['roll']
            capture = df_cleaned_record['capture']
            capture_id = '#'.join([season, site, roll, capture])
            df_cleaned_record['capture_id'] = capture_id
    # create image inventory
    image_inventory = dict()
    for image_row in df_cleaned_list:
        image_path = image_row['path']
        capture_id = image_row['capture_id']
        image_num = image_row['image']
        # skip more than 3 image cases (very rare)
        if int(image_num) > 3:
            continue
        if capture_id not in image_inventory:
            image_inventory[capture_id] = ['' for i in range(0, 3)]
        image_inventory[capture_id][int(image_num)-1] = image_path
    # create ML records
    ml_outputs = list()
    for df_report_row in df_report_list:
        capture_id = df_report_row['capture_id']
        main_data = [df_report_row[x] for x in output_header]
        # extract question data
        question_data = dict()
        for p, q in zip(questions_pfx, questions):
            try:
                question_data[q] = df_report_row[p]
            except:
                question_data[q] = ''
        # set highest behavior labels to 1
        behaviors = {k: v for k, v in question_data.items() if k in behavior_labels}
        behaviors = set_max_binary_to_one(behaviors)
        question_data.update(behaviors)
        # convert questions if necessary (e.g. binarize)
        question_data_converted = [convert_answer(question_data[q], question_types[q]) for q in questions]
        image_paths = image_inventory[capture_id]
        ml_row = main_data + image_paths + question_data_converted
        ml_outputs.append(ml_row)
    # write to disk
    df_out = pd.DataFrame(ml_outputs)
    df_out.columns = output_header + ['image1', 'image2', 'image3'] + questions
    sort_df_by_capture_id(df_out)
    df_out.to_csv(path_output, index=False)
    set_file_permission(path_output)


def create_ml_files_splitted(
        season_id, path_data, path_output_species,
        path_output_species_blank_balanced):
    df_data = pd.read_csv(path_data, dtype='str', index_col=None)
    df_data.fillna('', inplace=True)
    df_data_list = df_data.to_dict(orient='records')
    # loop over all records
    capture_record_count = Counter()
    for df_record in df_data_list:
        # map/group species
        species = df_record['species'].lower()
        species_grouped = species_mapping[species]['grouped']
        df_record['species'] = species_grouped
        df_record['species_original'] = species
        # create blank/non-blank
        # 'empty' because of compatibility with Panthera data
        if df_record['species'] == 'blank':
            df_record['is_blank'] = '1'
            df_record['empty'] = 'blank'
        else:
            df_record['is_blank'] = '0'
            df_record['empty'] = 'species'
        # create training split
        capture_id = df_record['capture_id']
        zero_one_hash = id_to_zero_one(capture_id)
        split_name = assign_zero_one_to_split(
            zero_one_hash, split_percent, split_names)
        df_record['split_name'] = '_'.join([split_name, season_id])
        # count records
        capture_record_count.update({capture_id})
    # output species only
    species_only = list()
    balanced_sampling_ids = list()
    for i, df_record in enumerate(df_data_list):
        if df_record['species'].lower() != 'blank':
            species_only.append(df_record)
            balanced_sampling_ids.append('species')
        else:
            balanced_sampling_ids.append('blank')
        capture_id = df_record['capture_id']
        df_record['n_ids_in_capture'] = capture_record_count[capture_id]
    # blanced sampling
    species_blank_stats = Counter(balanced_sampling_ids)
    least_common = species_blank_stats.most_common()[-1]
    percent = {s: least_common[1] / c for s, c in species_blank_stats.items()}
    species_blank_balanced = list()
    for i, df_record in enumerate(df_data_list):
        capture_id = df_record['capture_id']
        zero_one_hash = id_to_zero_one(capture_id)
        if df_record['species'].lower() == 'blank':
            if zero_one_hash <= percent['blank']:
                species_blank_balanced.append(df_record)
        elif zero_one_hash <= percent['species']:
            species_blank_balanced.append(df_record)
    # output
    df_species = pd.DataFrame(species_only)
    first_cols = df_data.columns.tolist()
    cols_sorted = first_cols + [x for x in df_species.columns if x not in first_cols]
    df_species = df_species[cols_sorted]
    df_species.to_csv(path_output_species, index=False)
    set_file_permission(path_output_species)
    df_species_blank_balanced = pd.DataFrame(species_blank_balanced)
    df_species_blank_balanced = df_species_blank_balanced[cols_sorted]
    df_species_blank_balanced.to_csv(path_output_species_blank_balanced, index=False)
    set_file_permission(path_output_species_blank_balanced)


for season_id, path_report in reports.items():
    location, season = season_id.split('_')
    path_cleaned = '/home/packerc/shared/season_captures/{}/cleaned/{}_cleaned.csv'.format(location, season_id)
    path_output = os.path.join(output_root_path, location, '{}_data.csv'.format(season_id))
    create_ml_file_all(path_report, path_cleaned, path_output)
    print("Wrote file to: {}".format(path_output))


for season_id, path_report in reports.items():
    location, season = season_id.split('_')
    path_data = os.path.join(output_root_path, location, '{}_data.csv'.format(season_id))
    path_output_species_blank_balanced = os.path.join(output_root_path, location, '{}_data_blank_species_balanced.csv'.format(season_id))
    path_output_species = os.path.join(output_root_path, location, '{}_data_species.csv'.format(season_id))
    create_ml_files_splitted(
        season_id, path_data, path_output_species,
        path_output_species_blank_balanced)
    print("Wrote to {}".format(path_output_species))
    print("Wrote to {}".format(path_output_species_blank_balanced))
