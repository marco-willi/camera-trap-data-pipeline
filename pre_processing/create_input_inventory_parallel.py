""" Check image files """
import os
import argparse
import logging
import time
import numpy as np
import pandas as pd
import copy
from datetime import datetime
from collections import OrderedDict
import traceback
from multiprocessing import Process, Manager
from PIL import Image
from PIL.ExifTags import TAGS as exif_map

from logger import setup_logger, create_logfile_name
from pre_processing.utils import file_creation_date, image_check_stats
from utils import slice_generator
from global_vars import pre_processing_flags as flags


# args = dict()
# args['root_dir'] = '/home/packerc/shared/albums/ENO/ENO_S1'
# args['output_csv'] = '/home/packerc/shared/season_captures/ENO/ENO_S1_captures_raw.csv'
# args['output_csv'] = '/home/packerc/will5448/image_inventory_overview.csv'
# args['season_id'] = ''
# args['n_processes'] = 16

if __name__ == '__main__':

    # Parse command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("--root_dir", type=str, required=True)
    parser.add_argument("--season_id", type=str, default="")
    parser.add_argument("--output_csv", type=str, required=True)
    parser.add_argument("--n_processes", type=int, default=4)
    args = vars(parser.parse_args())

    # image check paramters
    msg_width = 99

    # logging
    log_file_name = create_logfile_name('create_input_inventory')
    log_file_path = os.path.join(
        os.path.dirname(args['output_csv']), log_file_name)
    setup_logger(log_file_name)
    logger = logging.getLogger(__name__)

    if args['season_id'] == '':
        args['season_id'] = os.path.split(args['root_dir'])[1]
        logger.info("Updating 'season_id' with {}".format(
            args['season_id']))

    site_directory_names = os.listdir(args['root_dir'])

    image_inventory = OrderedDict()

    # Loop over site directories
    for site_directory_name in site_directory_names:
        current_dir_full_path = os.path.join(
            args['root_dir'], site_directory_name)
        roll_directory_names = os.listdir(current_dir_full_path)
        # Loop over roll directories
        for roll_directory_name in roll_directory_names:
            roll = roll_directory_name.split('_')[1].split('R')[1]
            roll_directory_path = os.path.join(
                current_dir_full_path, roll_directory_name)
            roll_directory_path_rel = os.path.join(
                site_directory_name, roll_directory_name)
            image_file_names = os.listdir(roll_directory_path)
            # Loop over image files
            for image_file_name in image_file_names:
                image_path = os.path.join(roll_directory_path, image_file_name)
                image_path_rel = os.path.join(
                    roll_directory_path_rel,
                    image_file_name)
                image_inventory[image_path] = {
                    'season': args['season_id'],
                    'site': site_directory_name,
                    'roll': roll,
                    'image_name_original': image_file_name,
                    'image_path_original': image_path,
                    'image_path_original_rel': image_path_rel,
                    'datetime': '',
                    'date': '',
                    'time': '',
                    'exif_data': dict(),
                    'file_creation_date': '',
                    'image_has_failed_checks': '',
                    'exclude_image': '',
                    'image_check': {k: 0 for k in flags['image_checks']}
                }

    def process_image_batch(i, image_paths_batch, image_inventory, results):
        n_images_total = len(image_paths_batch)
        for img_no, image_path in enumerate(image_paths_batch):
            current_data = copy.deepcopy(image_inventory[image_path])
            current_checks = current_data['image_checks']
            # try to open the image
            try:
                img = Image.open(image_path)
            except:
                current_checks['corrupt_file'] = 1
            # read EXIF data
            try:
                exif = img._getexif()
            except:
                current_checks['corrupt_exif'] = 1
            # check EXIF data
            if exif is None:
                current_checks['empty_exif'] = 1
            else:
                exif_mapped = {
                    exif_map[k]: v for k, v in exif.items()
                    if k in exif_map}
                current_data['exif_data'].update(exif_mapped)
                # Extract time-stamp from exif data
                for exif_data_field in flags['exif_data_timestamps']:
                    if exif_data_field in current_data['exif_data']:
                        exif_date_str = current_data['exif_data'][exif_data_field]
                        dt_object = datetime.strptime(
                            exif_date_str,
                            flags['time_formats']['exif_input_datetime_format'])
                        exif_datetime = \
                            dt_object.strftime(
                               flags['time_formats']['output_datetime_format'])
                        exif_date = \
                            dt_object.strftime(
                                flags['time_formats']['output_date_format'])
                        exif_time = \
                            dt_object.strftime(
                                flags['time_formats']['output_time_format'])
                        current_data['datetime'] = exif_datetime
                        current_data['date'] = exif_date
                        current_data['time'] = exif_time
                        continue
            # get file creation date
            img_creation_date = file_creation_date(image_path)
            img_creation_date_str = time.strftime(
                flags['time_formats']['output_datetime_format'],
                time.gmtime(img_creation_date))
            current_data['file_creation_date'] = img_creation_date_str
            # check for uniformly colored images
            black_percent = \
                flags['image_check_parameters']['all_black']['percent']
            white_percent = \
                flags['image_check_parameters']['all_white']['percent']
            black_thresh = \
                flags['image_check_parameters']['all_black']['thresh']
            white_thresh = \
                flags['image_check_parameters']['all_white']['thresh']
            # check other aspects of the image
            pixel_data = np.asarray(img)
            n_pixels_total = np.multiply(
                pixel_data.shape[0], pixel_data.shape[1])
            # check for black pixels
            pixels_2D = np.sum(pixel_data < black_thresh, axis=(2))
            n_pixels_affected = np.sum(pixels_2D == 3)
            p_pixels_affected = n_pixels_affected / n_pixels_total
            is_black = (p_pixels_affected > black_percent)
            if is_black:
                current_checks['all_black'] = 1
            # check for white images
            pixels_2D = np.sum(pixel_data > white_thresh, axis=(2))
            n_pixels_affected = np.sum(pixels_2D == 3)
            p_pixels_affected = n_pixels_affected / n_pixels_total
            is_white = (p_pixels_affected > white_percent)
            if is_white:
                current_checks['all_white'] = 1
            # add flag indicating at least one failed check
            current_data['image_has_failed_checks'] = \
                max([v for v in current_data['image_checks'].values()])
            # add (preliminary) flag for images to exclude
            current_data['exclude_image'] = \
                current_data['image_has_failed_checks']
            results[image_path] = current_data
            if (img_no % 100) == 0:
                print("Process {:2} - Processed {}/{} images".format(
                    i, img_no, n_images_total))

    # Loop over all images
    image_paths_all = list(image_inventory.keys())
    n_images_total = len(image_paths_all)

    # parallelize image checking into 'n_processes'
    manager = Manager()
    results = manager.dict()
    try:
        processes_list = list()
        n_processes = min(args['n_processes'], n_images_total)
        slices = slice_generator(n_images_total, n_processes)
        for i, (start_i, end_i) in enumerate(slices):
            pr = Process(target=process_image_batch,
                         args=(i, image_paths_all[start_i:end_i],
                               image_inventory,
                               results))
            pr.start()
            processes_list.append(pr)
        for p in processes_list:
            p.join()
    except Exception:
        print(traceback.format_exc())

    for image_path, image_data in image_inventory.items():
        image_inventory[image_path] = results[image_path]

    image_check_stats(image_inventory, logger)

    # create csv
    image_inventory_flattened = dict()
    for image_path, image_data in image_inventory.items():
        _dat_standard = \
            {k: v for k, v in image_data.items() if not isinstance(v, dict)}
        _dat_flatt = dict()
        for image_key, image_value in image_data.items():
            if isinstance(image_value, dict):
                for k, v in image_value.items():
                    composite_key = '{}__{}'.format(image_key, k)
                    _dat_flatt[composite_key] = v
        image_inventory_flattened[image_path] = {
            **_dat_standard, **_dat_flatt}

    # Convert to Pandas DataFrame for exporting
    df = pd.DataFrame.from_dict(image_inventory_flattened, orient='index')

    # re-arrange columns
    cols = df.columns.tolist()
    first_cols = [
        'season', 'site', 'roll', 'image_path_original_rel']
    cols_rearranged = first_cols + [x for x in cols if x not in first_cols]
    df = df[cols_rearranged]

    # sort rows
    df.sort_values(by=first_cols, inplace=True)

    # export
    df.to_csv(args['output_csv'], index=False)

    # change permmissions to read/write for group
    os.chmod(args['output_csv'], 0o660)
