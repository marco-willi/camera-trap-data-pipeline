""" Check image files """
import os
import argparse
import logging
import time
import numpy as np
import copy
from collections import OrderedDict
import traceback
from multiprocessing import Process, Manager
from PIL import Image

from logger import setup_logger, create_log_file
from pre_processing.utils import (
    file_creation_date, image_check_stats, p_pixels_above_threshold,
    p_pixels_below_threshold, export_inventory_to_csv)
from utils import slice_generator, estimate_remaining_time
from config.cfg import cfg


flags = cfg['pre_processing_flags']

# args = dict()
# args['root_dir'] = '/home/packerc/shared/albums/ENO/ENO_S1'
# args['output_csv'] = '/home/packerc/shared/season_captures/ENO/ENO_S1_captures_raw.csv'
# #args['output_csv'] = '/home/packerc/will5448/image_inventory_overview.csv'
# args['season_id'] = ''
# args['n_processes'] = 16

if __name__ == '__main__':

    # Parse command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("--root_dir", type=str, required=True)
    parser.add_argument(
        "--season_id", type=str, default="",
        help="identifier that is exported to the inventory")
    parser.add_argument("--output_csv", type=str, required=True)
    parser.add_argument("--n_processes", type=int, default=4)
    parser.add_argument("--log_dir", type=str, default=None)
    args = vars(parser.parse_args())

    # image check paramters
    msg_width = 99

    # check existence of root dir
    if not os.path.isdir(args['root_dir']):
        raise FileNotFoundError(
            "root_dir {} does not exist -- must be a directory".format(
                args['root_dir']))

    # Logging
    if args['log_dir'] is not None:
        log_file_dir = args['log_dir']
    else:
        log_file_dir = os.path.dirname(args['output_csv'])
    log_file_path = create_log_file(
        log_file_dir,
        'create_image_inventory')
    setup_logger(log_file_path)
    logger = logging.getLogger(__name__)

    if args['season_id'] == '':
        last_dir = os.path.basename(os.path.normpath(args['root_dir']))
        args['season_id'] = last_dir
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
                    'file_creation_date': '',
                    **{'image_check__{}'.format(k):
                        0 for k in flags['image_checks']}}

    def process_image_batch(i, image_paths_batch, image_inventory, results):
        n_images_total = len(image_paths_batch)
        start_time = time.time()
        for img_no, image_path in enumerate(image_paths_batch):
            current_data = copy.deepcopy(image_inventory[image_path])
            # try to open the image
            try:
                img = Image.open(image_path)
            except:
                img = None
                current_data['image_check__corrupt_file'] = 1
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
            try:
                pixel_data = np.asarray(img)
                p_pixels_white = p_pixels_above_threshold(
                    pixel_data, white_thresh)
                p_pixels_black = p_pixels_below_threshold(
                    pixel_data, black_thresh)
                is_black = (p_pixels_black > black_percent)
                is_white = (p_pixels_white > white_percent)
                if is_black:
                    current_data['image_check__all_black'] = 1
                if is_white:
                    current_data['image_check__all_white'] = 1
            except:
                pass
            results[image_path] = current_data
            if (img_no % 100) == 0:
                est_t = estimate_remaining_time(
                    start_time, n_images_total, img_no)
                print("Process {:2} - Processed {}/{} images - ETA: {}".format(
                      i, img_no, n_images_total, est_t))
        print("Process {:2} - Finished".format(i))

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

    export_inventory_to_csv(image_inventory, args['output_csv'])
