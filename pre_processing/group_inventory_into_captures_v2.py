""" Group Input into Captures """
import numpy as np
import os
import argparse
from datetime import datetime
import logging

from pre_processing.utils import (
    image_check_stats, read_image_inventory,
    export_inventory_to_csv, update_time_checks)
from config.cfg import cfg
from logger import create_log_file, setup_logger


flags = cfg['pre_processing_flags']


# args = dict()
# args['inventory'] = '/home/packerc/will5448/data/pre_processing_tests/ENO_S1_inventory.csv'
# args['output_csv'] = '/home/packerc/will5448/data/pre_processing_tests/ENO_S1_captures_TEST.csv'
# args['log_dir'] = '/home/packerc/will5448/data/pre_processing_tests/'
# args['no_older_than_year'] = 2017
# args['no_newer_than_year'] = 2019


def create_new_image_path(image_data):
    """ Create new image path """
    image_dir = os.path.dirname(image_data['image_path_original'])
    new_name = create_new_image_name(image_data)
    return os.path.join(image_dir, new_name)


def create_new_image_path_rel(image_data):
    """ Create new image path """
    image_dir = os.path.dirname(image_data['image_path_original_rel'])
    new_name = create_new_image_name(image_data)
    return os.path.join(image_dir, new_name)


def create_new_image_name(image_data):
    """ Create a new image new based on image_data:
        - PLN_S1_A01_R1_IMAG0001.JPG
    """
    season = image_data['season']
    site = image_data['site']
    roll = 'R{}'.format(image_data['roll'])
    image_no_rank = 'IMAG{:04}'.format(image_data['image_rank_in_roll'])
    ending = '.{}'.format(image_data['image_name_original'].split('.')[1])
    new_name = '_'.join([season, site, roll, image_no_rank])
    return ''.join([new_name, ending])


def group_images_into_site_and_roll(inventory):
    # Group images into site and roll
    site_roll_inventory = dict()
    for image_id, image_data in inventory.items():
        # if image_data['datetime'] == '':
        #     continue
        season = image_data['season']
        site = image_data['site']
        roll = image_data['roll']
        season_site_roll_key = '#'.join([season, site, roll])
        if season_site_roll_key not in site_roll_inventory:
            site_roll_inventory[season_site_roll_key] = dict()
        site_roll_inventory[season_site_roll_key][image_id] = image_data
    return site_roll_inventory


def calculate_time_deltas(inventory, flags):
    """ Calulate time deltas between subsequent images """
    # group images into site and roll
    site_roll_inventory = group_images_into_site_and_roll(inventory)
    image_time_deltas = dict()
    # iterate over each roll individually
    for season_site_roll_key, site_roll_data in site_roll_inventory.items():
        # get all images from the current site and roll
        times = list()
        paths = list()
        # iterate over each image in a roll
        for image_id, image_data in site_roll_data.items():
            # if exif time not available take file creation time
            if image_data['datetime'] == '':
                img_time = image_data['file_creation_date']
            else:
                img_time = image_data['datetime']
            times.append(img_time)
            paths.append(image_id)
        # Define the order of the images by 1) time and 2) by name
        datetimes = [
            datetime.strptime(
                x,
                flags['time_formats']['output_datetime_format'])
            for x in times]
        times_seconds = [
            (x-datetime(1970, 1, 1)).total_seconds()
            for x in datetimes]
        ordered_indexes = np.lexsort((paths, times_seconds))
        # Re-order by the newly defined order
        paths_ordered = [paths[i] for i in ordered_indexes]
        times_seconds_ordered = [times_seconds[i] for i in ordered_indexes]
        # Calculate time deltas between subsequent images
        # (next and previous) in seconds and days
        delta_seconds_next_ordered = [
            (times_seconds_ordered[i+1] - times_seconds_ordered[i])
            for i in range(0, len(times_seconds_ordered)-1)]
        delta_days_next_ordered = [
            '{:.2f}'.format((x / (60*60*24)))
            for x in delta_seconds_next_ordered]
        delta_days_next_ordered.append(0)
        delta_seconds_next_ordered.append(0)
        # calculate times to next image
        delta_seconds_last_ordered = [
            abs(times_seconds_ordered[i] - times_seconds_ordered[i-1])
            for i in range(1, len(times_seconds_ordered))]
        delta_days_last_ordered = [
            '{:.2f}'.format((x / (60*60*24)))
            for x in delta_seconds_last_ordered]
        delta_days_last_ordered.insert(0, 0)
        delta_seconds_last_ordered.insert(0, 0)
        # loop over all deltas
        # (starting with the delta between first and second)
        image_rank_in_roll_ordered = [1]
        for i, delta in enumerate(delta_seconds_last_ordered):
            image_rank_in_roll_ordered.append(i+2)
        # add information to inventory
        for i in range(0, len(paths_ordered)):
            image_time_deltas[paths_ordered[i]] = {
                'image_rank_in_roll': image_rank_in_roll_ordered[i],
                'seconds_to_next_image_taken': delta_seconds_next_ordered[i],
                'seconds_to_last_image_taken': delta_seconds_last_ordered[i],
                'days_to_last_image_taken': delta_days_last_ordered[i],
                'days_to_next_image_taken': delta_days_next_ordered[i]}
    return image_time_deltas


# Group images into site and roll
def group_images_into_captures_by_time_delta(inventory, flags):
    """ Group images into capture events by time deltas"""
    site_roll_inventory = group_images_into_site_and_roll(inventory)
    image_to_capture = dict()
    for season_site_roll_key, site_roll_data in site_roll_inventory.items():
        # order images by time
        image_to_order = {
            k: v['image_rank_in_roll']
            for k, v in site_roll_data.items()}
        images_sorted = sorted(image_to_order.items(), key=lambda x: x[1])
        # initialize captures and ranks
        capture_ids_ordered = [1]
        image_rank_in_capture_ordered = [1]
        current_capture = 1
        current_rank_in_capture = 1
        # loop over all deltas
        # (starting with the delta between first and second)
        for i, (img_name, rank) in enumerate(images_sorted[1:]):
            delta = inventory[img_name]['seconds_to_last_image_taken']
            if delta <= flags['general']['capture_delta_seconds']:
                current_rank_in_capture += 1
            else:
                current_rank_in_capture = 1
                current_capture += 1
            capture_ids_ordered.append(current_capture)
            image_rank_in_capture_ordered.append(current_rank_in_capture)
        for i, (image_name, rank) in enumerate(images_sorted):
            image_to_capture[image_name] = {
                'capture': capture_ids_ordered[i],
                'image_rank_in_capture': image_rank_in_capture_ordered[i]
            }
    return image_to_capture


def update_inventory_with_capture_data(inventory, image_to_capture):
    """ update inventory with capture data """
    # merge capture info with inventory
    # and determine new image names
    for image_path_original, image_capture_data in image_to_capture.items():
        # add capture information
        inventory[image_path_original].update(image_capture_data)


def update_inventory_with_image_names(inventory):
    """ Create new image names """
    for image_data in inventory.values():
        image_data['image_path'] = \
            create_new_image_path(image_data)
        image_data['image_name'] = \
            create_new_image_name(image_data)
        image_data['image_path_rel'] = \
            create_new_image_path_rel(image_data)


def update_time_checks_inventory(inventory, flags):
    """ Update time check flags in inventory """
    for image_id, image_data in inventory.items():
        try:
            update_time_checks(image_data, flags)
        except:
            pass


if __name__ == '__main__':

    # Parse command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("--inventory", type=str, required=True)
    parser.add_argument("--output_csv", type=str, required=True)
    parser.add_argument("--no_older_than_year", type=int, default=1970)
    parser.add_argument("--no_newer_than_year", type=int, default=9999)
    parser.add_argument("--log_dir", type=str, default=None)
    args = vars(parser.parse_args())

    # image check paramters
    msg_width = 99

    # Logging
    if args['log_dir'] is not None:
        log_file_dir = args['log_dir']
    else:
        log_file_dir = os.path.dirname(args['output_csv'])
    log_file_path = create_log_file(
        log_file_dir,
        'group_inventory_into_captures')
    setup_logger(log_file_path)
    logger = logging.getLogger(__name__)

    # update time checks
    time_checks = flags['image_check_parameters']
    time_checks['time_too_old']['min_year'] = args['no_older_than_year']
    time_checks['time_too_new']['max_year'] = args['no_newer_than_year']

    inventory = read_image_inventory(
        args['inventory'],
        unique_id='image_path_original')

    # calculate time_deltas
    time_deltas = calculate_time_deltas(inventory, flags)
    update_inventory_with_capture_data(inventory, time_deltas)

    # group images into captures
    image_to_capture = group_images_into_captures_by_time_delta(inventory, flags)

    update_inventory_with_capture_data(inventory, image_to_capture)

    update_inventory_with_image_names(inventory)

    update_time_checks_inventory(inventory, flags)

    image_check_stats(inventory, logger)

    export_inventory_to_csv(inventory, args['output_csv'])
