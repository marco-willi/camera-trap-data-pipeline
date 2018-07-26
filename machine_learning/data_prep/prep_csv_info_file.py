""" Create a CSV file with info about all images and labels to
    create dataset inventories from
"""
import csv
import datetime
from collections import Counter, OrderedDict
import argparse

from utils import (
    correct_image_name, id_to_zero_one,
    assign_zero_one_to_split)


def binarize(x):
    """ convert values between 0 and 1 to 1 (if 0.5 or larger), else to 0 """
    try:
        return int(float(x) + 0.5)
    except:
        return 0


if __name__ == '__main__':

    # Parse command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-season", type=str, required=True,
        help="season (1-9) or all")
    parser.add_argument(
        "-season_prefix", type=str, default='',
        help="prefix for the season identifier (e.g. SER_S)")
    parser.add_argument("-split_names", nargs='+', type=str,
                        help='split dataset into these named splits',
                        default=['train', 'val', 'test'],
                        required=False)
    parser.add_argument("-split_percent", nargs='+', type=float,
                        help='split dataset into these proportions',
                        default=[0.9, 0.05, 0.05],
                        required=False)
    parser.add_argument(
        "-max_n_images", type=int, default=3,
        help="maximum number of images per capture")

    args = vars(parser.parse_args())

    for k, v in args.items():
        print("Argument %s: %s" % (k, v))

    season = args['season']
    data_path = '/home/packerc/will5448/data/season_exports'
    input_db_export = '%s/db_export_season_%s.csv' % (data_path, season)
    output_cleaned = '%s/db_export_season_%s_cleaned.csv' % (data_path, season)
    max_images = args['max_n_images']

    behaviors = ["Standing", "Resting", "Moving",
                 "Eating", "Interacting", "Babies"]

    # Read db export file
    all_records = list()
    counts = list()
    with open(input_db_export, 'r') as f:
        csv_reader = csv.reader(f, delimiter=',')
        header = next(csv_reader)
        header.append("empty")
        header[header.index("idCaptureEvent")] = 'capture_id'
        header[header.index("CountMedian")] = 'Count'
        header[header.index("PathFilename")] = 'image'
        header.append('split_name')
        header.append('location')
        header_to_id = {h: i for i, h in enumerate(header)}
        for row in csv_reader:
            for _ in range(len(row), len(header)):
                row.append('')
            try:
                ts = datetime.datetime.strptime(
                        row[header_to_id["CaptureTimestamp"]],
                        '%Y-%m-%d %H:%M:%S')
            except:
                ts = datetime.datetime.strptime('1900', '%Y')
            row[header_to_id["CaptureTimestamp"]] = \
                ts.strftime('%Y-%m-%d-%H-%M-%S')
            # change path
            row[header_to_id['image']] = 'SER/' + \
                correct_image_name(row[header_to_id["image"]])
            # convert behaviors to binary
            for behav in behaviors:
                row[header_to_id[behav]] = binarize(row[header_to_id[behav]])
            # convert empty non-empty
            if row[header_to_id["NumberOfSpecies"]] == '0':
                row[header_to_id["empty"]] = '1'
                row[header_to_id["Species"]] = 'empty'
                row[header_to_id["Count"]] = '0'
            else:
                row[header_to_id["empty"]] = '0'
                if row[header_to_id["Count"]] == '0':
                    print("Wrong count for: %s" % row)
            counts.append(row[header_to_id["Count"]])
            # lower case for species
            row[header_to_id["Species"]] = row[header_to_id["Species"]].lower()
            # add location
            row[header_to_id["location"]] = row[header_to_id["GridCell"]]
            # Season with prefix
            row[header_to_id["Season"]] = args['season_prefix'] + row[header_to_id["Season"]]
            # create capture id
            capture_id = '#'.join([row[header_to_id["Season"]],
                                   row[header_to_id["GridCell"]],
                                   row[header_to_id["RollNumber"]],
                                   row[header_to_id["CaptureEventNum"]]])
            row[header_to_id['capture_id']] = capture_id
            # randomly assign to test / train / val
            zero_one_hash = id_to_zero_one(capture_id)
            split_name = assign_zero_one_to_split(
                zero_one_hash,
                args['split_percent'], args['split_names'])
            row[header_to_id["split_name"]] = '_'.join([split_name, row[header_to_id["Season"]].lower()])
            all_records.append(row)

    # check counts
    Counter(counts)

    # Convert and Clean data
    data_clean = OrderedDict()
    for row in all_records:
        capture_id = row[header_to_id['capture_id']]
        if capture_id not in data_clean:
            data_clean[capture_id] = {'images': list(), 'record': dict(),
                                      'species': set()}
        dat = data_clean[capture_id]
        img = row[header_to_id['image']]
        if (img not in dat['images']) and (len(dat['images']) < max_images):
            dat['images'].append(img)
        dat['species'].add(row[header_to_id['Species']])
        dat['record'][row[header_to_id['Species']]] = row

    # Create list for writing to disk
    data_list_clean = list()
    images = ['image%s' % (i + 1) for i in range(0, max_images)]
    header_clean = ['capture_id', 'empty', 'Species', 'Count', 'Standing',
                    'Resting', 'Moving', 'Eating', 'Interacting',
                    'Babies', 'Season', 'CaptureTimestamp'] + images
    record_clean = ['' for i in range(0, len(header_clean))]
    record_mapper = {v: k for k, v in enumerate(header_clean)}
    for k, v in data_clean.items():
        new_record = [x for x in record_clean]
        # fill in images
        for i, img in enumerate(v['images']):
            new_record[record_mapper['image%s' % (i + 1)]] = img
        # create a record per species
        for spec in v['species']:
            row = v['record'][spec]
            for col in header_clean:
                if 'image' in col:
                    continue
                new_record[record_mapper[col]] = row[header_to_id[col]]
            to_append = [x for x in new_record]
            data_list_clean.append(to_append)

    # write file
    with open(output_cleaned, "w") as outs:
        csv_writer = csv.writer(outs, delimiter=',')
        print("Writing file to %s" % output_cleaned)
        _ = csv_writer.writerow([x.lower() for x in header_clean])
        for i, line in enumerate(data_list_clean):
            _ = csv_writer.writerow(line)




# Counter({'0': 353793, '1': 44584, '2': 11435, '3': 5388, '4': 3092,
# '11-50': 2108, '5': 1995, '6': 1291, '7': 990, '8': 737, '10': 511,
# '9': 460, '51+': 6})


# Target output
# capture_id, image_path, empty, species, behaviors, season, site, location, timestamp

# meta data
#/home/packerc/shared/season_captures/SER/captures
# Season, Site, Roll, Capture, Image, PathFilename, TimestampJPG
# 1,B04,1,1,1,S1/B04/B04_R1/PICT0001.JPG,2010:07:18 16:26:14

# season_x.csv
# S9/B03/B03_R1/S9_B03_R1_IMAG0003.JPG,ASG001lfjx,21,1,1,0,0,0,0,0

# season exports
# idCaptureEvent,Season,GridCell,RollNumber,CaptureEventNum,SequenceNum,PathFilename
# 2424940,9,B03,1,1,1,S9/B03/B03_R1/S9_B03_R1_IMAG0001.JPG
