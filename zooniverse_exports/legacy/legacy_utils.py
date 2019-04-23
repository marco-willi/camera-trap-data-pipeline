""" Create an inventory for timestams for all images / captures form S1-S10 """
import os
import pandas as pd
import csv
import json
from collections import OrderedDict
from collections import Counter
from datetime import datetime

from zooniverse_exports.legacy.legacy_extractor import build_img_path
from utils.utils import correct_image_name


#################################
# Functions
#################################

def create_capture_id(season, site, roll, capture):
    return 'SER_{}#{}#{}#{}'.format(season, site, roll, capture)


# add additional columns
def create_date(date_str):
    try:
        tm = _get_datetime_obj(date_str)
    except:
        return ''
    return tm.strftime("%Y-%m-%d")


def create_time(date_str):
    try:
        tm = _get_datetime_obj(date_str)
    except:
        return ''
    return tm.strftime("%H:%M:%S")


def _get_datetime_obj(date_str):
    """ Get DateTime object from a str with unknown format """
    try:
        time_obj = datetime.strptime(date_str, '%Y:%m:%d %H:%M:%S')
    except ValueError:
        try:
            time_obj = datetime.strptime(
                date_str,
                '%Y-%m-%d %H:%M:%S')
        except ValueError:
            try:
                time_obj = datetime.strptime(
                    date_str,
                    '%Y-%m-%d %H:%M:%SZ')
            except ValueError:
                print(
                    "could not convert {} to datetime".format(date_str))
    return time_obj


def read_db(path_images_db, col_mapper):
    """ Read data from MSI SQL db export """
    df = pd.read_csv(path_images_db, dtype=str)
    df.fillna('', inplace=True)
    df.rename(columns=col_mapper, inplace=True)
    df = df[[
        'subject_id', 'season', 'site', 'roll', 'capture', 'SequenceNum',
        'PathFilename', 'TimestampJPG', 'TimestampFile',
        'TimestampAccepted', 'idImage', 'Invalid',
        'ZooniverseStatus', 'idTimestampStatuses',
        'StatusDescription']]
    df.drop_duplicates(subset='PathFilename', inplace=True)
    season = ['S{}'.format(x) for x in df['season']]
    df['season'] = season
    df['image_path'] = df['PathFilename'].apply(correct_image_name)
    return df


def read_lila(lila_path):
    """ Read data from LILA json export """
    with open(lila_path, 'r') as f:
        lila_data = json.load(f)
    species_map = {x['id']: x['name'] for x in lila_data['categories']}
    image_to_capture = {x['id']:
        {'image_path': x['file_name'], 'subject_id': x['seq_id'],
         'season': x['season'], 'site': x['location'],
         'datetime': x.get('datetime', '')} for x in lila_data['images']}
    capture_to_species = dict()
    for anno in lila_data['annotations']:
        subject_id = image_to_capture[anno['image_id']]['subject_id']
        if not subject_id in capture_to_species:
            capture_to_species[subject_id] = set()
        capture_to_species[subject_id].add(species_map[anno['category_id']])
    rows = list()
    cols_imgs = ['image_path', 'subject_id', 'season', 'site', 'datetime']
    for img_id, img_data in image_to_capture.items():
        species = '#'.join(capture_to_species[img_data['subject_id']])
        row = [img_data[x] for x in cols_imgs]
        row.append(species)
        rows.append(row)
    df = pd.DataFrame(rows)
    cols_all = cols_imgs
    cols_all.append('species')
    df.columns = cols_all
    return df


def read_cleaned(path_cleaned):
    """ Read Data from Cleaned CSV files """
    cleaned = list()
    for season in [4, 5, 6, 7, 8, 9, 10]:
        print("Starting with {}".format(season))
        path = os.path.join(path_cleaned, 'S{}_cleaned.csv'.format(season))
        df_dict = OrderedDict()
        with open(path, 'r') as f:
            csv_reader = csv.reader(f, delimiter=',', quotechar='"')
            header = next(csv_reader)
            mapper = {x: i for i, x in enumerate(header)}
            for line_no, line in enumerate(csv_reader):
                record = {k: line[v] for k, v in mapper.items()}
                record['ImageName'] = os.path.split(record['path'])[-1]
                record['season'] = 'S{}'.format(season)
                record['PathFilename'] = build_img_path(
                    record['season'], record['site'],
                    record['roll'], record['ImageName'])
                old_time_ob = _get_datetime_obj(record['oldtime'])
                record['oldtime'] = old_time_ob.strftime("%Y-%m-%d %H:%M:%S")
                df_dict[line_no] = record
        df = pd.DataFrame.from_dict(df_dict, orient='index')
        cleaned.append(df)
    df_cleaned = pd.concat(cleaned)
    df_cleaned.fillna('', inplace=True)
    return df_cleaned


# Simple Comparisons
def print_stats(df_stats):
    stats = Counter()
    for _id in df_stats.index:
        stats[_id] = df_stats[_id]
    total = sum([x for x in stats.values()])
    for answer, count in stats.most_common():
        print("Category: {:20} -- counts: {:10} / {} ({:.2f} %)".format(
            answer, count, total, 100*count/total))


def stats_df(df_stats):
    stats = Counter()
    data = list()
    for _id in df_stats.index:
        stats[_id] = df_stats[_id]
    total = sum([x for x in stats.values()])
    for answer, count in stats.most_common():
        data.append([answer, count, total, round(100*count/total, 3)])
    df = pd.DataFrame(data)
    df.columns = ['species', 'count', 'total', 'percentage']
    return df
