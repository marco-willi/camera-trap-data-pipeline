""" Create a Manifest """
import csv
import json
import os
import argparse
from collections import OrderedDict

# For Testing
# args = dict()
# args['cleaned_captures_csv'] = "/home/packerc/shared/season_captures/RUA/cleaned/RUA_S1_cleaned.csv"
# args['compressed_image_dir'] = "/home/packerc/shared/zooniverse/ToUpload/RUA_will5448/RUA_S1_Compressed/"
# args['output_manifest_dir'] = "/home/packerc/shared/zooniverse/Manifests/RUA/"
# args['manifest_prefix'] = 'RUA_S1'
# args['csv_quotechar'] = '"'
# args['attribution'] = 'University of Minnesota Lion Center + SnapshotSafari + Ruaha Carnivore Project + Tanzania + Ruaha National Park'
# args['license'] =  'SnapshotSafari + Ruaha Carnivore Project'


if __name__ == "__main__":

    # Parse command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("-cleaned_captures_csv", type=str, required=True)
    parser.add_argument("-compressed_image_dir", type=str, required=True)
    parser.add_argument("-output_manifest_dir", type=str, required=True)
    parser.add_argument("-manifest_prefix", type=str, required=True)
    parser.add_argument("-attribution", type=str, required=True)
    parser.add_argument("-license", type=str, required=True)
    parser.add_argument("-csv_quotechar", type=str, default='"')

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

    if not os.path.exists(args['cleaned_captures_csv']):
        raise FileNotFoundError("cleaned_captures_csv: %s not found" %
                                args['cleaned_captures_csv'])

    if '.' in args['manifest_prefix']:
        raise ValueError("manifest_prefix must not contain a dot")

    manifest_file_name = args['manifest_prefix'] + '_manifest.json'
    manifest_path = os.path.join(args['output_manifest_dir'],
                                 manifest_file_name)

    if os.path.exists(manifest_path):
        raise FileExistsError("manifest already exists: %s" % manifest_path)

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

    # Find all processed images
    images_on_disk = set(os.listdir(args['compressed_image_dir']))

    # Create a Manifest which is a dictionary / json like structure
    # containing all information about the dataset

    manifest = OrderedDict()
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
        valid_codes = ('0', '3')
        # Skip image if not in valid codes
        if invalid not in valid_codes:
            continue
        # Skip if image is not on disk
        if image_name not in images_on_disk:
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

    # Export Manifest
    with open(manifest_path, 'w') as outfile:
        first_row = True
        for _id, values in manifest.items():
            if first_row:
                outfile.write('{')
                outfile.write('"%s":' % _id)
                json.dump(values, outfile)
                first_row = False
            else:
                outfile.write(',\n')
                outfile.write('"%s":' % _id)
                json.dump(values, outfile)
        outfile.write('}')

# with open(manifest_path, 'r') as f:
#     mani = json.load(f)

# Read the Manifest
# mani = OrderedDict()
# with open(manifest_path, 'r') as f:
#     for line in f:
#         dict_entry = json.loads(line)
#         mani.update(dict_entry)
