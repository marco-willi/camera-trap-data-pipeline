""" Copy Images from one Directory to another while Processing them
    - resizing and compressing
    - uses multiprocessing (default 24 processes)
"""
import csv
import os
import sys
import argparse
from PIL import Image
from collections import OrderedDict
import traceback
import time
from multiprocessing import Process, Manager

from utils import estimate_remaining_time, slice_generator


###############################
# Image Compression and
# multiprocessing Functions
###############################


def compress_images(pid, image_source_list,
                    image_dest_list,
                    result_dict,
                    save_quality=None,
                    max_pixel_of_largest_side=None):
    """ Compresses images for use with multiprocessing

        Arguments:
        -----------
        pid (int):
            the id of the process for status printing
        image_source_list (list):
            image source paths
        image_source_list (list):
            image destination paths
        results_dict (dict):
            shared dictionary to store results into
        save_quality (int):
            compression quality of images
        max_pixel_of_largest_side (int):
            max allowed size in pixels of largest side of an image,
            if an image exceeds this, its largest side is resized to this
            while preserving the aspect ratio
    """
    # Check Input
    assert any([save_quality, max_pixel_of_largest_side]) is not None,\
        "At least one of save_quality or max_pixel_of_largest_side must be \
         specified"
    if save_quality is not None:
        assert (save_quality <= 100) and (save_quality > 0), \
            "save_quality must be between 1 and 100"
    print("PID %s is using parameters: %s %s" %
          (pid, save_quality, max_pixel_of_largest_side))
    # Loop over all images and process each
    counter = 0
    n_tot = len(image_source_list)
    start_time = time.time()
    for source, dest in zip(image_source_list, image_dest_list):
        if (counter % 2000) == 0:
            print("Process ID %s - done %s/%s - estimated time remaining: %s" %
                  (pid, counter, n_tot,
                   estimate_remaining_time(start_time, n_tot, counter)))
            sys.stdout.flush()
        try:
            img = Image.open(source)
            # Check largest side of image and resize if necessary
            if max_pixel_of_largest_side is not None:
                if any([x > max_pixel_of_largest_side for x in img.size]):
                    img.thumbnail(size=[max_pixel_of_largest_side,
                                        max_pixel_of_largest_side],
                                  resample=1)
            if save_quality is not None:
                img.save(dest, "JPEG",
                         quality=save_quality)
            else:
                img.save(dest)
            img.close()
            # save result "Successful Compression"
            result_dict[source] = 'SC'
        except:
            # save result "Not Compressed"
            print("Failed to compress %s" % source)
            result_dict[source] = 'CR'
        counter += 1
    # Print process end status
    print("Process " + str(pid) + "  has finished")


def process_images_multiprocess(
        image_source_list,
        image_dest_list,
        image_process_function,
        n_processes=4,
        **kwargs):
    """ Processes a list of images using multiprocessing
        Arguments:
        ----------
        image_source_list (list):
            list of source image paths
        image_dest_list (list):
            list of destination image paths, order must be the same as
            image_source_list
        image_process_function (func):
            a function to process images, takes as input:
            pid (int), image_source_list, image_dest_list,
            status_messages (dict), additional keyword arguments
        n_processes (int): the number of processes to use
    """
    n_records = len(image_source_list)
    # Shared dictionary to store status messages for each record
    manager = Manager()
    status_messages = manager.dict()
    # initialize with empty messages
    for f in image_source_list:
        status_messages[f] = ''
    try:
        processes_list = list()
        slices = slice_generator(n_records, n_processes)
        for i, (start_i, end_i) in enumerate(slices):
            pr = Process(target=compress_images,
                         args=(i, image_source_list[start_i:end_i],
                               image_dest_list[start_i:end_i],
                               status_messages),
                         kwargs=kwargs)
            pr.start()
            processes_list.append(pr)
        for p in processes_list:
            p.join()
    except Exception:
        print(traceback.format_exc())

    return status_messages


# For testing
# args = dict()
# args['cleaned_captures_csv'] = "D:\\Studium_GD\\Zooniverse\\SnapshotSafari\\data\\season_captures\\RUA\\cleaned\\RUA_S1_cleaned.csv"
# args['csv_quotechar'] = '"'
# args['output_image_dir'] = "/home/packerc/shared/zooniverse/ToUpload/RUA/Compressed_S1/"
# args['root_image_path'] = '/home/packerc/shared/albums/SER/'

if __name__ == "__main__":

    # Parse command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("-cleaned_captures_csv", type=str, required=True)
    parser.add_argument("-output_image_dir", type=str, required=True)
    parser.add_argument("-root_image_path", type=str, required=True)
    parser.add_argument("-n_processes", type=int, default=24, required=False)
    parser.add_argument("-max_image_pixel_side", type=int, default=1440)
    parser.add_argument("-image_quality", type=int, default=50)
    parser.add_argument("-csv_quotechar", type=str, default='"')

    args = vars(parser.parse_args())

    for k, v in args.items():
        print("Argument %s: %s" % (k, v))

    # Check Inputs
    if not os.path.isdir(args['root_image_path']):
        raise FileNotFoundError("root_image_path: %s is not a directory" %
                                args['root_image_path'])

    if not os.path.isdir(args['output_image_dir']):
        raise FileNotFoundError("output_image_dir: %s is not a directory" %
                                args['output_image_dir'])

    if not os.path.exists(args['cleaned_captures_csv']):
        raise FileNotFoundError("cleaned_captures_csv: %s not found" %
                                args['cleaned_captures_csv'])

    if not ((args['image_quality'] > 0) and (args['image_quality'] <= 100)):
        raise ValueError("image_quality has to be between 1 and 100")

    # Read Season Captures CSV
    cleaned_captures = list()
    with open(args['cleaned_captures_csv'], newline='') as csvfile:
        csv_reader = csv.reader(csvfile, delimiter=',',
                                quotechar=args['csv_quotechar'])
        for _id, row in enumerate(csv_reader):
            if _id == 0:
                header = row
                name_to_id_mapper = {x: i for i, x in enumerate(header)}
            else:
                cleaned_captures.append(row)

    print("Found %s images in %s" %
          (len(cleaned_captures), args['cleaned_captures_csv']))

    # Define source and destination paths for all images
    images = OrderedDict()
    for img in cleaned_captures:
        img_name = img[name_to_id_mapper['imname']]
        img_path = img[name_to_id_mapper['path']]
        images[img_name] = {
            'source': os.path.join(args['root_image_path'], img_path),
            'dest': os.path.join(args['output_image_dir'], img_name)
            }

    # Remove already processed files
    files_in_dest = os.listdir(args['output_image_dir'])

    print("Found %s images in %s" %
          (len(files_in_dest), args['output_image_dir']))

    if len(files_in_dest) > 0:
        for file in files_in_dest:
            images.pop(file, None)

    # Create source and destination lists
    image_source_path_list = list()
    image_dest_path_list = list()

    for value in images.values():
        image_source_path_list.append(value['source'])
        image_dest_path_list.append(value['dest'])

    # run parallelized image compression and return status messages
    status_results = process_images_multiprocess(
        image_source_path_list,
        image_dest_path_list,
        compress_images,
        n_processes=args['n_processes'],
        save_quality=args['image_quality'],
        max_pixel_of_largest_side=args['max_image_pixel_side']
    )
