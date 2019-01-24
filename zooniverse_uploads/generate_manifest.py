""" Create a Manifest - Information about capture-events for uploading to
    Zooniverse
"""
import os
import argparse
from collections import OrderedDict

from utils import (
    export_dict_to_json_with_newlines,
    read_cleaned_season_file, file_path_generator)

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
        "--compressed_image_dir", type=str, required=True,
        help="Path to a directory with all images as referenced in the \
              captures_csv")
    parser.add_argument(
        "--output_manifest_dir", type=str, required=True,
        help="Output directory to write the manifest into.")
    parser.add_argument(
        "--manifest_id", type=str, required=True,
        help="A unique identifier for the manifest, e.g,\
              RUA_S1. Typically, this is used for a season of data and \
              describes the content of the captures_csv.")
    parser.add_argument(
        "--attribution", type=str, required=True,
        help="Attribution text.")
    parser.add_argument(
        "--license", type=str, required=True,
        help="license information")
    parser.add_argument(
        "--csv_quotechar", type=str, default='"',
        help="Quotechar used to import the captures_csv")

    args = vars(parser.parse_args())

    for k, v in args.items():
        print("Argument %s: %s" % (k, v))

    # Check Inputs
    if not os.path.isdir(args['output_manifest_dir']):
        raise FileNotFoundError("output_manifest_dir: %s is not a directory" %
                                args['output_manifest_dir'])

    if not os.path.isdir(args['compressed_image_dir']):
        raise FileNotFoundError("compressed_image_dir: %s is not a directory" %
                                args['compressed_image_dir'])

    if not os.path.exists(args['captures_csv']):
        raise FileNotFoundError("captures_csv: %s not found" %
                                args['captures_csv'])

    if any([x in args['manifest_id'] for x in ['.', '__']]):
        raise ValueError("manifest_id must not contain any of '.'/'__'")

    manifest_path = file_path_generator(
        dir=args['output_manifest_dir'],
        id=args['manifest_id'],
        name="manifest")

    if os.path.exists(manifest_path):
        raise FileExistsError("manifest already exists: %s" % manifest_path)

    # Read Season Captures CSV
    cleaned_captures, name_to_id_mapper = \
        read_cleaned_season_file(args['captures_csv'],
                                 args['csv_quotechar'])

    print("Found %s images in %s" %
          (len(cleaned_captures), args['captures_csv']))

    # Find all processed images
    images_on_disk = set(os.listdir(args['compressed_image_dir']))

    # Create the manifest
    manifest = OrderedDict()
    omitted_images_counter = 0
    images_not_found_counter = 0
    valid_codes = ('0', '3')
    for row in cleaned_captures:
        # Extract important fields
        season = row[name_to_id_mapper['season']]
        site = row[name_to_id_mapper['site']]
        roll = row[name_to_id_mapper['roll']]
        capture = row[name_to_id_mapper['capture']]
        image_no = row[name_to_id_mapper['image']]
        image_name = row[name_to_id_mapper['imname']]
        image_path = row[name_to_id_mapper['path']]
        invalid = row[name_to_id_mapper['invalid']]
        # Skip image if not in valid codes
        if invalid not in valid_codes:
            omitted_images_counter += 1
            continue
        # Skip if image is not on disk
        if image_name not in images_on_disk:
            images_not_found_counter += 1
            continue
        # unique capture id
        capture_id = '#'.join([season, site, roll, capture])
        # Create a new entry in the manifest
        if capture_id not in manifest:
            # generate metadata for uploading to Zooniverse
            upload_metadata = {
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
            images = {
                'original_images': [],
                'compressed_images': []
            }
            manifest[capture_id] = {
                'upload_metadata': upload_metadata, 'info': info,
                'images': images}
        # Add image information
        image_disk_path = os.path.join(
            args['compressed_image_dir'], image_name)
        manifest[capture_id]['images']['compressed_images'].append(
            image_disk_path)
        manifest[capture_id]['images']['original_images'].append(
            image_path)

    print("Omitted %s images due to invalid code in 'invalid' column" %
          omitted_images_counter)
    print("Number of images not found in images folder %s" %
          images_not_found_counter)
    print("Writing %s captures to %s" % (len(manifest.keys()), manifest_path))

    export_dict_to_json_with_newlines(manifest, manifest_path)

    # change permmissions to read/write for group
    os.chmod(manifest_path, 0o660)
