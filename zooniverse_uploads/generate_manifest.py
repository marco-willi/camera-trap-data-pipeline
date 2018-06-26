""" Create a Manifest """
import csv
import json
import os
import argparse
from collections import OrderedDict

# For Testing
args = dict()
args['cleaned_captures_csv'] = "/home/packerc/shared/zooniverse/season_captures/RUA/cleaned/RUA_S1_cleaned.csv"
args['input_image_dir'] = "/home/packerc/shared/zooniverse/ToUpload/RUA/Compressed_S1/"
args['output_manifest_dir'] = "/home/packerc/shared/zooniverse/Manifests/RUA/"
args['manifest_id'] = 'RUA_S1'
args['csv_quotechar'] = '"'
args['attribution'] = 'University of Minnesota Lion Center + SnapshotSafari + Ruaha Carnivore Project + Tanzania + Ruaha National Park'
args['license'] =  'SnapshotSafar + Ruaha Carnivore Project'


if __name__ == "__main__":

    # Parse command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("-cleaned_captures_csv", type=str, required=True)
    parser.add_argument("-input_image_dir", type=str, required=True)
    parser.add_argument("-output_manifest_dir", type=str, required=True)
    parser.add_argument("-manifest_id", type=str, required=True)
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

    if not os.path.isdir(args['input_image_dir']):
        raise FileNotFoundError("input_image_dir: %s is not a directory" %
                                args['input_image_dir'])

    if not os.path.exists(args['cleaned_captures_csv']):
        raise FileNotFoundError("cleaned_captures_csv: %s not found" %
                                args['cleaned_captures_csv'])

    if '.' in args['manifest_id']:
        raise ValueError("manifest_name must not contain a dot")

    manifest_file_name = args['manifest_id'] + '_manifest.json'
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
    images = set(os.listdir(args['output_image_dir']))

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
        invalid = row[name_to_id_mapper['invalid']]

        exclude_invalid_codes = (0, 3)

        # Skip image if invalid code
        if invalid in exclude_invalid_codes:
            continue

        # Skip if image is not on disk
        if image_name not in images:
            continue

        # unique capture id
        capture_id = '#'.join([season, site, roll, capture])

        # Create a new entry in the manifest
        if capture_id not in manifest:

            # generate metadata
            metadata = {
                '#site': site,
                '#roll': roll,
                '#capture': capture,
                'attribution': args['attribution'],
                'license': args['license']
            }

            # generate upload status
            status = {
                'uploaded': False
            }

            images = []

            manifest[capture_id] = {
                'metadata': metadata, 'status': status, 'images': images}

        # Add current image
        current_data = manifest[capture_id]
        image_disk_path = os.path.join(args['output_image_dir'], image_name)
        current_data['images'].append(image_disk_path)

    # Export Manifest
    with open(manifest_path, 'w') as outfile:
        for _id, values in manifest.items():
            json.dump({_id: values}, outfile)
            outfile.write('\n')
    # with open(manifest_path, 'w') as fp:
    #     json.dump(manifest, fp, indent=0)
