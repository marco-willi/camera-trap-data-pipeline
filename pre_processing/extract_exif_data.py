""" Extract EXIF Data """
import os
import argparse
import logging
import time
import traceback
import textwrap
import copy
import datetime
from multiprocessing import Process, Manager

import exiftool
import pandas as pd

from config.cfg import cfg
from logger import setup_logger, create_log_file
from pre_processing.utils import (
    export_inventory_to_csv, read_image_inventory)
from utils import (
    slice_generator, estimate_remaining_time, set_file_permission)


# args = dict()
# args['inventory'] = '/home/packerc/will5448/data/pre_processing_tests/ENO_S1_inventory.csv'
# args['update_inventory'] = True
# args['output_csv'] = '/home/packerc/will5448/data/pre_processing_tests/ENO_S1_captures_TEST_EXIF.csv'
# args['exiftool_path'] = '/home/packerc/will5448/software/Image-ExifTool-11.31/exiftool'
# args['n_processes'] = 4

flags = cfg['pre_processing_flags']


def _extract_meta_data(tags, groups=['EXIF', 'MakerNotes', 'Composite']):
    """ Specify which group of image meta-data to extract """
    return {k: v for k, v in tags.items()
            if any([k.startswith(g) for g in groups])}


def _prefix_meta_data(tags, prefix='exif__'):
    """ Specify a prefix for the meta-data """
    return {'{}{}'.format(prefix, k): v for k, v in tags.items()}


def _extract_time_info_from_exif(exif_tags, flags):
    """ Extract and convert exif datetime info """
    for exif_data_field in flags['exif_data_timestamps']:
        output = dict()
        try:
            exif_date_str = exif_tags[exif_data_field]
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
            output['datetime'] = exif_datetime
            output['date'] = exif_date
            output['time'] = exif_time
            return output
        except:
            pass
    raise ValueError("Failed to extract datetime info.")


if __name__ == '__main__':

    # Parse command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("--inventory", type=str, required=True)
    parser.add_argument("--update_inventory", action='store_true')
    parser.add_argument("--output_csv", type=str, default=None)
    parser.add_argument("--n_processes", type=int, default=4)
    parser.add_argument(
        "--exiftool_path", type=str,
        default='/home/packerc/will5448/software/Image-ExifTool-11.31/exiftool')
    parser.add_argument(
        "--log_dir", type=str, default=None)
    parser.add_argument(
        "--log_filename", type=str,
        default='extract_exif_data')
    args = vars(parser.parse_args())

    ######################################
    # Check Input
    ######################################

    if not os.path.isfile(args['inventory']):
        raise FileNotFoundError("inventory: {} not found".format(
                                args['inventory']))

    ######################################
    # Configuration
    ######################################

    msg_width = 99

    # logging
    if args['log_dir'] is not None:
        log_file_path = create_log_file(args['log_dir'], args['log_filename'])
        setup_logger(log_file_path)
    else:
        setup_logger()
    logger = logging.getLogger(__name__)

    for k, v in args.items():
        logger.info("Argument {}: {}".format(k, v))

    ######################################
    # Read Image Inventory
    ######################################

    image_inventory = read_image_inventory(
        args['inventory'],
        unique_id='image_path_original')

    ######################################
    # Process Inventory
    ######################################

    def extract_exif_image_list(i, image_paths_batch, results, exif_exec):
        """ Extract exif data from a list of images -
            write result into 'results' dictionary
        """
        n_images_total = len(image_paths_batch)
        start_time = time.time()
        with exiftool.ExifTool(executable_=exif_exec) as et:
            for img_no, img_path in enumerate(image_paths_batch):
                try:
                    tags = et.execute_json(img_path)[0]
                except Exception:
                    print(traceback.format_exc())
                    tags = None
                results[img_path] = tags
                if (img_no % 100) == 0:
                    est_t = estimate_remaining_time(
                        start_time, n_images_total, img_no)
                    msg = textwrap.shorten(
                        "Process {:2} - Processed {}/{} images - \
                         ETA: {}".format(
                         i, img_no, n_images_total, est_t), width=msg_width)
                    print(msg)
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
            pr = Process(target=extract_exif_image_list,
                         args=(i, image_paths_all[start_i:end_i],
                               results, args['exiftool_path']))
            pr.start()
            processes_list.append(pr)
        for p in processes_list:
            p.join()
    except Exception:
        print(traceback.format_exc())

    # copy the shared dictionary
    exif_all = {k: v for k, v in results.items()}

    # Update Image Inventory
    if args['update_inventory']:
        # Update Image Inventory with EXIF data
        for img_name in image_paths_all:
            current_data = copy.deepcopy(image_inventory[img_name])
            try:
                exif_data = exif_all[img_name]
                if exif_data is None:
                    current_data.update({'image_check__corrupt_exif': 1})
                    logger.info(
                        "could not read exif data for image: {}".format(
                            img_name))
                elif len(exif_data.keys()) == 0:
                    logger.info(
                        "exif data for image: {} empty".format(
                            img_name))
                    current_data.update({'image_check__empty_exif': 1})
                else:
                    selected_exif = _extract_meta_data(exif_data)
                    prefixed_exif = _prefix_meta_data(selected_exif)
                    try:
                        time_info = _extract_time_info_from_exif(
                            prefixed_exif, flags)
                        current_data.update(time_info)
                    except:
                        logger.warning(
                            "Failed to extract datetime info from {}".format(
                                img_name
                            ))
                    current_data.update(prefixed_exif)
            except:
                current_data.update({'image_check__corrupt_exif': 1})
            image_inventory[img_name] = current_data

        export_inventory_to_csv(image_inventory, args['output_csv'])

    # Export EXIF Data separately
    if args['output_csv'] is not None:
        df = pd.DataFrame.from_dict(exif_all, orient='index')
        df.index.name = 'image_path_original'
        # export
        df.to_csv(args['output_csv'], index=True)
        # change permmissions to read/write for group
        set_file_permission(args['output_csv'])
