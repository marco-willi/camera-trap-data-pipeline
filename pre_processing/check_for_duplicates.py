""" Check for duplicate files in a root_directory
    root_directory:
        - site_directory:
            - roll_directory:
                - files
    Credit to: https://stackoverflow.com/a/36113168
"""
import os
import hashlib
import argparse
import logging

from logger import setup_logger, create_log_file


def chunk_reader(fobj, chunk_size=1024):
    """Generator that reads a file in chunks of bytes"""
    while True:
        chunk = fobj.read(chunk_size)
        if not chunk:
            return
        yield chunk


def get_hash(filename, first_chunk_only=False, hash=hashlib.sha1):
    hashobj = hash()
    file_object = open(filename, 'rb')
    if first_chunk_only:
        hashobj.update(file_object.read(1024))
    else:
        for chunk in chunk_reader(file_object):
            hashobj.update(chunk)
    hashed = hashobj.digest()
    file_object.close()
    return hashed


def check_for_duplicates(paths, hash=hashlib.sha1):
    hashes_by_size = {}
    hashes_on_1k = {}
    hashes_full = {}
    n_tot = len(paths)
    for i, path in enumerate(paths):
        file_size = os.path.getsize(path)
        duplicate = hashes_by_size.get(file_size)
        if duplicate:
            hashes_by_size[file_size].append(path)
        else:
            # create the list for this file size
            hashes_by_size[file_size] = []
            hashes_by_size[file_size].append(path)
        if ((i % 10000) == 0) and i > 0:
            print("Checked size of {}/{} files".format(i, n_tot))
    # For all files with the same file size, get their
    # hash on the 1st 1024 bytes
    logger.info("Checking for duplication by comparing small hashes ..")
    for __, files in hashes_by_size.items():
        if len(files) < 2:
            continue
        for filename in files:
            try:
                small_hash = get_hash(filename, first_chunk_only=True)
            except (OSError,):
                # the file access might've changed till the exec point got here
                continue
            duplicate = hashes_on_1k.get(small_hash)
            if duplicate:
                hashes_on_1k[small_hash].append(filename)
            else:
                # create the list for this 1k hash
                hashes_on_1k[small_hash] = []
                hashes_on_1k[small_hash].append(filename)
    # For all files with the hash on the 1st 1024 bytes, get their
    # hash on the full file - collisions will be duplicates
    n_duplicates = 0
    logger.info("Checking for duplication by comparing full hashes ..")
    for __, files in hashes_on_1k.items():
        # this hash of fist 1k file bytes is unique, no need to
        # spend cpy cycles on it
        if len(files) < 2:
            continue
        for filename in files:
            try:
                full_hash = get_hash(filename, first_chunk_only=False)
            except (OSError,):
                # the file access might've changed till the exec point got here
                continue
            duplicate = hashes_full.get(full_hash)
            if duplicate:
                logger.info("Duplicate found: %s and %s" %
                            (filename, duplicate))
                n_duplicates += 1
            else:
                hashes_full[full_hash] = filename
    logger.info("Found {} duplicates".format(n_duplicates))


if __name__ == '__main__':

    # Parse command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--root_dir", type=str, required=True,
        help="Root directory of the organized camera-trap data -- \
        contains the site folders.")
    parser.add_argument(
        "--log_dir", type=str, default=None)
    parser.add_argument(
        "--log_filename", type=str,
        default='check_for_duplicates')
    args = vars(parser.parse_args())

    # check existence of root dir
    if not os.path.isdir(args['root_dir']):
        raise FileNotFoundError(
            "root_dir {} does not exist -- must be a directory".format(
                args['root_dir']))

    # logging
    if args['log_dir'] is not None:
        log_file_path = create_log_file(args['log_dir'], args['log_filename'])
        setup_logger(log_file_path)
    else:
        setup_logger()
    logger = logging.getLogger(__name__)

    site_directory_names = os.listdir(args['root_dir'])

    all_image_paths = list()

    # Collect all image paths
    for site_directory_name in site_directory_names:
        site_full_path = os.path.join(
            args['root_dir'], site_directory_name)
        roll_directory_names = os.listdir(site_full_path)
        for roll_directory_name in roll_directory_names:
            roll_directory_path = os.path.join(
                site_full_path, roll_directory_name)
            image_file_names = os.listdir(roll_directory_path)
            for image_file_name in image_file_names:
                all_image_paths.append(
                    os.path.join(roll_directory_path, image_file_name))
    logger.info("Found {} images".format(len(all_image_paths)))

    # check for duplicates
    check_for_duplicates(all_image_paths, hash=hashlib.sha1)
