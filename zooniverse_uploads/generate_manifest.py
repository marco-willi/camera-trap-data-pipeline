""" Create a Manifest - Information about capture-events for uploading to
    Zooniverse
"""
import os
import argparse
from collections import OrderedDict
import logging

from utils.logger import setup_logger, create_log_file
from utils.utils import (
    export_dict_to_json_with_newlines,
    read_cleaned_season_file_df, file_path_generator, set_file_permission)


# For Testing
# args = dict()
# args['captures_csv'] = "/home/packerc/shared/season_captures/RUA/cleaned/RUA_S1_cleaned.csv"
# args['compressed_image_dir'] = "/home/packerc/shared/zooniverse/ToUpload/RUA_will5448/RUA_S1_Compressed/"
# args['output_manifest_dir'] = "/home/packerc/shared/zooniverse/Manifests/RUA/"
# args['manifest_id'] = 'RUA_S1'
# args['csv_quotechar'] = '"'
# args['attribution'] = 'University of Minnesota Lion Center + SnapshotSafari + Ruaha Carnivore Project + Tanzania + Ruaha National Park'
# args['license'] =  'SnapshotSafari + Ruaha Carnivore Project'
#
# args['captures_csv'] = "/home/packerc/shared/season_captures/GRU/cleaned/GRU_S1_cleaned.csv"
# args['compressed_image_dir'] = "/home/packerc/shared/zooniverse/ToUpload/GRU/GRU_S1_Compressed/"
# args['output_manifest_dir'] = "/home/packerc/shared/zooniverse/Manifests/GRU/"
# args['manifest_id'] = 'RUA_S1'
# args['csv_quotechar'] = '"'
# args['attribution'] = 'University of Minnesota Lion Center + Snapshot Safari + Singita Grumeti + Tanzania'
# args['license'] =  'Snapshot Safari + Singita Grumeti'


if __name__ == "__main__":

    # Parse command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--captures_csv", type=str, required=True,
        help="Path to the cleaned captures csv.")
    parser.add_argument(
        "--output_manifest_dir", type=str, required=True,
        help="Output directory to write the manifest into.")
    parser.add_argument(
        "--manifest_id", type=str, required=True,
        help="A unique identifier for the manifest, e.g,\
              RUA_S1. Typically, this is used for a season of data and \
              describes the content of the captures_csv.")
    parser.add_argument(
        "--images_root_path", type=str, default='',
        help="Root path of the column 'path' in the captures_csv. Used to \
        check if images exist on disk.")
    parser.add_argument(
        "--attribution", type=str, required=True,
        help="Attribution text.")
    parser.add_argument(
        "--license", type=str, required=True,
        help="license information")
    parser.add_argument(
        "--csv_quotechar", type=str, default='"',
        help="Quotechar used to import the captures_csv")
    parser.add_argument(
        "--log_dir", type=str, default=None)
    parser.add_argument(
        "--log_filename", type=str,
        default='generate_manifest')

    args = vars(parser.parse_args())

    # Check Inputs
    if not os.path.isdir(args['output_manifest_dir']):
        raise FileNotFoundError("output_manifest_dir: %s is not a directory" %
                                args['output_manifest_dir'])

    if not os.path.exists(args['captures_csv']):
        raise FileNotFoundError("captures_csv: %s not found" %
                                args['captures_csv'])

    if args['images_root_path'] != '':
        if not os.path.isdir(args['images_root_path']):
            raise FileNotFoundError("images_root_path: %s not found" %
                                    args['images_root_path'])

    if any([x in args['manifest_id'] for x in ['.', '__']]):
        raise ValueError("manifest_id must not contain any of '.'/'__'")

    # logging
    if args['log_dir'] is not None:
        log_file_path = create_log_file(args['log_dir'], args['log_filename'])
        setup_logger(log_file_path)
    else:
        setup_logger()
    logger = logging.getLogger(__name__)

    for k, v in args.items():
        logger.info("Argument {}: {}".format(k, v))

    manifest_path = file_path_generator(
        dir=args['output_manifest_dir'],
        id=args['manifest_id'],
        name="manifest")

    if os.path.exists(manifest_path):
        raise FileExistsError("manifest already exists: %s" % manifest_path)

    # Read Season Captures CSV
    cleaned_captures = read_cleaned_season_file_df(args['captures_csv'])

    logger.info("Found %s images in %s" %
                (cleaned_captures.shape[0], args['captures_csv']))

    # Create the manifest
    manifest = OrderedDict()
    omitted_images_counter = 0
    images_not_found_counter = 0
    invalid_codes = ('1', '2')
    n_records_total = cleaned_captures.shape[0]
    for row_no, row in cleaned_captures.iterrows():
        # Extract important fields
        season = row.season
        site = row.site
        roll = row.roll
        capture = row.capture
        image_path = row.path
        invalid = row.invalid
        # unique capture id
        try:
            capture_id = row.capture_id
        except:
            capture_id = '#'.join([season, site, roll, capture])
        # Skip image if code indicates invalid code
        if invalid in invalid_codes:
            omitted_images_counter += 1
            continue
        # Skip if image is not on disk
        image_path_full = os.path.join(args['images_root_path'], image_path)
        if not os.path.isfile(image_path_full):
            images_not_found_counter += 1
            logger.warning("Image not found: {}".format(image_path_full))
            continue
        # Create a new entry in the manifest
        if capture_id not in manifest:
            # generate metadata for uploading to Zooniverse
            upload_metadata = {
                '#capture_id': capture_id,
                '#site': site,
                '#roll': roll,
                '#season': season,
                '#capture': capture,
                'attribution': args['attribution'],
                'license': args['license']
            }
            # store additional information
            info = {
                'uploaded': False
            }
            manifest[capture_id] = {
                'upload_metadata': upload_metadata,
                'info': info,
                'images': []}
        # Add image information
        manifest[capture_id]['images'].append(image_path)

        if (row_no % 10000) == 0:
            logger.info("Processed {}/{} records".format(
                row_no, n_records_total))

    logger.info("Omitted %s images due to invalid code in 'invalid' column" %
                omitted_images_counter)
    logger.info("Number of images not found in images folder %s" %
                images_not_found_counter)
    logger.info("Writing %s captures to %s" %
                (len(manifest.keys()), manifest_path))

    export_dict_to_json_with_newlines(manifest, manifest_path)

    # change permmissions to read/write for group
    set_file_permission(manifest_path)
