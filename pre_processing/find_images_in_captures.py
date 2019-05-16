""" Match and find images in the captures file with images provides in a
    directory - Use case:
    - find specific images (e.g. sensitive rhino images) that have been
      copied to a separate folder but were processed with the normal scripts
      to flag them for 'no_upload' in the action list
"""
import os
import argparse
import logging

import pandas as pd

from utils.utils import list_pictures, get_hash
from pre_processing.utils import (
    read_image_inventory)
from utils.logger import set_logging


logger = logging.getLogger(__name__)


# # example path:
# args = dict()
# args['captures_csv'] = '/home/packerc/shared/season_captures/ENO/captures/ENO_S1_captures_updated.csv'
# args['images_to_match_path'] = '/home/packerc/will5448/data/pre_processing_tests/test_images/'
# args['output_csv'] = '/home/packerc/will5448/data/pre_processing_tests/image_matches.csv'


def path_to_size(paths):
    """ Create dict with path to file size"""
    path_to_size = {}
    for i, path in enumerate(paths):
        file_size = os.path.getsize(path)
        path_to_size[path] = file_size
    return path_to_size


def eliminate_ambigous_size_matches(matches):
    """ Eliminate ambigous matches (same size) by comparing file hashes """
    # eliminate ambiguous matches
    for path in matches.keys():
        size_matches = matches[path]
        hash_matches = list()
        if len(size_matches) > 1:
            hash_to_find = get_hash(path, first_chunk_only=False)
            for file in size_matches:
                try:
                    hash_to_match = get_hash(file, first_chunk_only=False)
                except (OSError,):
                    continue
                if hash_to_match == hash_to_find:
                    hash_matches.append(file)
            matches[path] = hash_matches


if __name__ == '__main__':

    # Parse command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("--captures", type=str, required=True)
    parser.add_argument("--images_to_match_path", type=str, required=True)
    parser.add_argument("--output_csv", type=str, default=None)
    args = vars(parser.parse_args())

    # Check Input
    if not os.path.isfile(args['captures']):
        raise FileNotFoundError("captures: {} not found".format(
                                args['captures']))

    if not os.path.isdir(args['images_to_match_path']):
        raise FileNotFoundError(
            "images_to_match_path: {} must be a directory".format(
             args['images_to_match_path']))

    # logging
    set_logging()

    # find all images
    images_to_find = list_pictures(
        args['images_to_match_path'], ext=('jpg', 'jpeg'))

    logger.info("Found {} images in {}".format(
        len(images_to_find), args['images_to_match_path']))

    captures = read_image_inventory(
        args['captures_csv'],
        unique_id='image_path')

    logger.info("Read {} with {} images".format(
        args['captures_csv'], len(captures.keys())))

    images_to_search_in = list(captures.keys())

    matches = {path: [] for path in images_to_find}

    logger.info("Get file sizes for images to find...")
    to_find_size = path_to_size(images_to_find)
    logger.info("Get file sizes for images to search in...")
    to_search_size = path_to_size(images_to_search_in)

    # invert dictionary: size -> file names list
    size_to_find = dict()
    for key, value in to_find_size.items():
        size_to_find.setdefault(value, list()).append(key)

    size_to_search = dict()
    for key, value in to_search_size.items():
        size_to_search.setdefault(value, list()).append(key)

    logger.info("Matching files based on file size...")
    for size, files_to_find in size_to_find.items():
        if size in size_to_search:
            size_matches = size_to_search[size]
            for files_to_find in files_to_find:
                matches[files_to_find] += size_matches

    eliminate_ambigous_size_matches(matches)

    # all duplicates
    logger.info(
        "Seached duplicates for {} images".format(len(matches.keys())))
    logger.info(
        "Found duplicates for {} images".format(
            sum([len(x) > 0 for x in matches.items()])))

    # export
    if args['output_csv'] is not None:
        logger.info("Exporting matches to: {}".format(args['output_csv']))
        found_to_match = {v[0]: k for k, v in matches.items()}
        df = pd.DataFrame.from_dict(found_to_match, orient="index")
        df.reset_index(inplace=True)
        df.columns = ['image_path', 'image_path_search']
        df['image_name'] = df['image_path'].apply(
            lambda x: os.path.basename(x))
        df.to_csv(args['output_csv'], index=False)
        logger.info("Exported {} records to: {}".format(
            df.shape[0], args['output_csv']))
