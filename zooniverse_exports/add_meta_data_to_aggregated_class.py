""" Add meta data to aggregted zooniverse classifications
    - to create (preliminary) reports
    - to create machine learning (tfrecord) files
"""
import os
import csv
import argparse
import datetime

from collections import Counter

from utils import assign_zero_one_to_split, id_to_zero_one
from global_vars import label_mappings


# # Manifest
# site,roll,capture,Image 1,Image 2,Image 3,zoosubjsetid,zoosubjid,uploadstatus
# J04,1,1,2305_8919_8239.JPG,6117_6926_0493.JPG,1368_0048_6842.JPG,18231,17510211,UC
#
# # Season cleaned
# season,site,roll,capture,image,path,timestamp,oldtime,sr,imname,invalid
# GRU_S1,J05,1,14,1,GRU_S1/J05/J05_R1/GRU_S1_J05_R1_IMAG0036.JPG,2017:06:06 03:56:50,2017:06:06 03:56:50,J05_R1,GRU_S1_J05_R1_IMAG0036.JPG,1
# GRU_S1,J06,1,17,1,GRU_S1/J06/J06_R1/GRU_S1_J06_R1_IMAG0043.JPG,2017:06:09 22:28:38,2017:06:09 22:28:38,J06_R1,GRU_S1_J06_R1_IMAG0043.JPG,1
#
# # aggregated
# subject_id,label_num,species,count,moving,eating,standing,resting,interacting,young_present
# 17512921,1,WILDEBEEST,10,1,0,1,0,0,1
#
# # Result
# capture_id,empty,species,count,standing,resting,moving,eating,interacting,babies,season,capturetimestamp,location,split_name,image1,image2,image3
# SER_S1

# args = dict()
# args['classifications_aggregated'] = '/home/packerc/shared/machine_learning/data/zooniverse_exports/GRU/GRU_S1/classifications_aggregated.csv'
# args['season_cleaned'] = ['/home/packerc/shared/season_captures/GRU/cleaned/GRU_S1_cleaned.csv']
# args['output_csv'] = '/home/packerc/will5448/data/season_exports/db_export_gru_season_1.csv'
# args['season'] = 'GRU_S1'
# args['manifest_files_old'] = ['/home/packerc/shared/zooniverse/Manifests/GRU/GRU_S1_manifest_v1']
# args['max_n_images'] = 3
# args['manifest_file_new'] = None


if __name__ == '__main__':

    # Parse command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("-classifications_aggregated", type=str, required=True)
    parser.add_argument("-season", type=str, required=True, help="e.g GRU_S1")
    parser.add_argument("-site", type=str, required=True, help="e.g GRU")
    parser.add_argument("-manifest_files_old", default=None, nargs='+', type=str)
    parser.add_argument("-manifest_file_new", default=None, type=str)
    parser.add_argument("-season_cleaned", default=None, nargs='+', type=str)
    parser.add_argument("-max_n_images", default=3, type=int)

    parser.add_argument("-output_csv", type=str, required=True)

    args = vars(parser.parse_args())

    output_header = ['capture_id', 'empty', 'species', 'count', 'standing',
                     'resting', 'moving', 'eating', 'interacting', 'babies',
                     'season', 'capturetimestamp', 'location',
                     'split_name'] + \
                    ['image%s' % i for i in range(1, args['max_n_images']+1)]

    class_header = ['subject_id', 'label_num', 'species', 'count', 'moving',
                    'eating', 'standing', 'resting', 'interacting',
                    'young_present']

    def _remove_quotes_from_list(lst):
        return [x.strip('"') for x in lst]

    # Read Cleaned Season Files
    captures = dict()
    for season_cleaned_file in args['season_cleaned']:
        with open(season_cleaned_file, newline='') as csvfile:
            reader = csv.reader(csvfile, delimiter=',')
            header = next(reader)
            header = _remove_quotes_from_list(header)
            col_mapping = {x: i for i, x in enumerate(header)}
            for row_id, row in enumerate(reader):
                    row = _remove_quotes_from_list(row)
                    season = row[col_mapping['season']]
                    site = row[col_mapping['site']]
                    roll = row[col_mapping['roll']]
                    capture = row[col_mapping['capture']]
                    # unique capture id
                    capture_id = '#'.join([season,
                                           site,
                                           roll,
                                           capture])
                    # timestamp
                    try:
                        ts = datetime.datetime.strptime(
                                row[col_mapping['timestamp']],
                                '%Y:%m:%d %H:%M:%S')
                    except:
                        ts = datetime.datetime.strptime('1900', '%Y')
                    # image path
                    image = row[col_mapping['path']]
                    # add site to image path
                    image = os.path.join(args['site'], image)
                    image_num = row[col_mapping['image']]
                    # add record
                    if capture_id in captures:
                        captures[capture_id]['images'].append(image)
                    else:
                        captures[capture_id] = {
                            'season': season,
                            'capturetimestamp': ts.strftime('%Y-%m-%d-%H-%M-%S'),
                            'location': site,
                            'images': [image]
                        }

    if args['manifest_files_old'] is not None:
        mapping = dict()
        for manifest_file in args['manifest_files_old']:
            with open(manifest_file, newline='') as csvfile:
                reader = csv.reader(csvfile, delimiter=',')
                header = next(reader)
                col_mapping = {x: i for i, x in enumerate(header)}
                for row_id, row in enumerate(reader):
                    subject_id = row[col_mapping['zoosubjid']]
                    site = row[col_mapping['site']]
                    roll = row[col_mapping['roll']]
                    capture = row[col_mapping['capture']]
                    # unique capture id
                    capture_id = '#'.join([args['season'],
                                           site,
                                           roll,
                                           capture])
                    mapping[subject_id] = capture_id
    elif args['manifest_file_new'] is not None:
        raise NotImplementedError("manifest_file_new processing not yet \
            implemented")
    else:
        raise ValueError("at least one of manifest_files_old and \
            manifest_file_new must be specified")

    # Read Aggregated Classifications
    aggregated = dict()
    with open(args['classifications_aggregated'], newline='') as csvfile:
        reader = csv.reader(csvfile, delimiter=',')
        header = next(reader)
        col_mapping = {x: i for i, x in enumerate(header)}
        for row_id, row in enumerate(reader):
            subject_id = row[col_mapping['subject_id']]
            aggregated[subject_id] = \
                {x: row[col_mapping[x]] for x in class_header}

    # Build final record
    final = list()
    for subject_id, label_data in aggregated.items():
        # get capture_id
        try:
            capture_id = mapping[subject_id]
        except:
            continue
        # get meta data
        meta_data = captures[capture_id]
        # all data
        record_data = {**meta_data, **label_data}
        record_data['capture_id'] = capture_id
        record_data['babies'] = record_data['young_present']
        # assign capture id to test/val/train split
        hash = id_to_zero_one(capture_id)
        split = assign_zero_one_to_split(hash, [0.9, 0.1, 0.1],
                                         ['train', 'val', 'test'])
        record_data['split_name'] = '_'.join([split, season.lower()])
        # images
        images = ['image%s' % i for i in range(1, args['max_n_images']+1)]
        for i in range(0, args['max_n_images']):
            try:
                record_data['image%s' % (i+1)] = record_data['images'][i]
            except:
                record_data['image%s' % (i+1)] = ''
        # map species
        if record_data['species'] == 'NOTHINGHERE':
            record_data['empty'] = 'empty'
            record_data['species'] = 'empty'
        else:
            record_data['empty'] = 'species'
        record_data['species'] = record_data['species'].lower()
        # map counts
        if record_data['count'] in label_mappings['counts_db_to_ml']:
            record_data['count'] = label_mappings['counts_db_to_ml'][record_data['count']]
        # build record
        row = [record_data[x] for x in output_header]
        final.append(row)

    print("Processed %s capture events" % len(final))

    # print all species
    all_species = list()
    for f in final:
        all_species.append(f[2])
    Counter(all_species)

    # print all counts
    all_counts = list()
    for f in final:
        all_counts.append(f[3])
    Counter(all_counts)

    with open(args['output_csv'], "w", newline='') as outs:
        csv_writer = csv.writer(outs, delimiter=',')
        print("Writing file to %s" % args['output_csv'])
        _ = csv_writer.writerow(output_header)
        for row in final:
            _ = csv_writer.writerow(row)
