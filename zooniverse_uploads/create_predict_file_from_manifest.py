""" Create a Prediction File from a Manifest for a Model to
    Generate Predictions
"""
import csv
import json
import os
import argparse

# For Testing
# args = dict()
# args['manifest'] = "/home/packerc/shared/zooniverse/Manifests/RUA/RUA_S1_manifest.json"
# args['prediction_file'] = "/home/packerc/shared/machine_learning/data/info_files/RUA/RUA_S1/RUA_S1_new.csv"


if __name__ == "__main__":

    # Parse command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("-manifest", type=str, required=True)
    parser.add_argument("-prediction_file", type=str, required=True)

    args = vars(parser.parse_args())

    for k, v in args.items():
        print("Argument %s: %s" % (k, v))

    # Check Inputs
    prediction_file_path = os.path.split(args['prediction_file'])[0]
    if not os.path.isdir(prediction_file_path):
        raise FileNotFoundError("Path to store predictions: %s is not a \
                                directory" %
                                prediction_file_path)

    if not os.path.exists(args['manifest']):
        raise FileNotFoundError("manifest: %s not found" %
                                args['manifest'])

    # Read the Manifest
    with open(args['manifest'], 'r') as f:
        manifest = json.load(f)

    print("Found %s capture events in %s" %
          (len(manifest.keys()), args['manifest']))

    # Extract all image paths and store them to disk
    with open(args['prediction_file'], "w", newline='') as f:
        print("Writing file to %s" % args['prediction_file'])
        for capture_id, mani_data in manifest.items():
            for image in mani_data['images']['original_images']:
                f.write(image + '\n')
