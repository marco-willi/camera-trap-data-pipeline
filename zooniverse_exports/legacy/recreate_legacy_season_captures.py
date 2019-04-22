""" Re-Create Season Captures from Zooniverse Exports

Input:
--------
capture,capture_id,created_at,filenames,retired_at,retirement_reason,roll,season,site,timestamps,subject_id
1,SER_S9#B03#1#1,2016-05-24 03:35:47 UTC,S9/B03/B03_R1/S9_B03_R1_IMAG0001.JPG;S9/B03/B03_R1/S9_B03_R1_IMAG0002.JPG,,blank_consensus,1,S9,B03,2014-06-09
07:54:03;2014-06-09 07:54:05,ASG001ko0u
10,SER_S9#B03#1#10,2016-05-02 13:26:23 UTC,S9/B03/B03_R1/S9_B03_R1_IMAG0015.JPG;S9/B03/B03_R1/S9_B03_R1_IMAG0016.JPG;S9/B03/B03_R1/S9_B03_R1_IMAG0017.JP
G,,blank_consensus,1,S9,B03,2014-06-16 14:54:57;2014-06-16 14:54:57;2014-06-16 14:54:57,ASG001hqfu

"""
import os
import pandas as pd
import argparse
import logging

from utils.logger import setup_logger, create_log_file


def unpackNames(names):
    return names.split(';')


def extract_date_and_time(datetime):
    if datetime == '':
        return '', ''
    elif datetime.endswith('UTC'):
        date, time, _ = datetime.split(' ')
    elif 'T' in datetime:
        date, time = datetime.split('T')
    elif ' ' in datetime:
        date, time = datetime.split(' ')
    else:
        raise ValueError("datetime {} not recognized".format(datetime))
    if '-' in time:
        time, offset = time.split('-')
    return date, time


if __name__ == '__main__':

    # Parse command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("--subjects_extracted", type=str, required=True)
    parser.add_argument("--output_csv", type=str, required=True)
    parser.add_argument(
        "--log_dir", type=str, default=None)
    parser.add_argument(
        "--log_filename", type=str,
        default='recreate_legacy_season_captures')

    args = vars(parser.parse_args())

    # check existence of root dir
    if not os.path.isfile(args['subjects_extracted']):
        raise FileNotFoundError(
            "subjects_extracted {} does not exist -- must be a file".format(
                args['subjects_extracted']))

    # logging
    if args['log_dir'] is not None:
        log_file_path = create_log_file(args['log_dir'], args['log_filename'])
        setup_logger(log_file_path)
    else:
        setup_logger()
    logger = logging.getLogger(__name__)

    output_header = [
        'sort_id', 'capture_id', 'season', 'site',
        'roll', 'capture', 'image', 'path', 'timestamp']

    df = pd.read_csv(args['subjects_extracted'], dtype=str)
    df.fillna('', inplace=True)
    header = list(df.columns)
    season_captures = list()
    empty_captures = 0
    for i, row in df.iterrows():
        capture = row[header.index('capture')]
        if capture == '':
            empty_captures += 1
            continue
        capture_id = row[header.index('capture_id')]
        roll = row[header.index('roll')]
        season = row[header.index('season')]
        site = row[header.index('site')]
        timestamps = row[header.index('timestamps')]
        filenames = row[header.index('filenames')]
        timestamps_list = unpackNames(timestamps)
        filenames_list = unpackNames(filenames)
        if len(filenames_list) != len(timestamps_list):
            logger.info("Filenames not equal Timestamps")
            break
        for img_num, (fn, ts) in enumerate(zip(filenames_list, timestamps_list)):
            date, time = extract_date_and_time(ts)
            datetime = ' '.join([date, time])
            image = img_num+1
            sort_id = '{}#{}#{}#{:05}#{:05}'.format(
                season, site, roll, int(capture), int(image))
            img_row = [
                sort_id, capture_id, season,
                site, roll, capture, image, fn, datetime]
            season_captures.append(img_row)
    df_new = pd.DataFrame(season_captures, columns=output_header)
    df_new.sort_values(['sort_id'], inplace=True)
    df_new.drop('sort_id', inplace=True, axis=1)
    df_new.to_csv(args['output_csv'], index=False)
    logger.info(
        "Wrote: {}  - {} subjects not exported due to missing info".format(
            args['output_csv'], empty_captures))
