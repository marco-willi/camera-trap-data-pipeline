""" Create a Prediction File from a Manifest for a Model to
    Generate Predictions

    Arguments:
    ----------
    manifest: Path to a manifest (.json)
    prediction_file: Path to the new file that is generated for calculating
        predictions(.csv)
"""
import json
import os
import csv
import argparse

# For Testing
# args = dict()
# args['manifest'] = "/home/packerc/shared/zooniverse/Manifests/RUA/RUA_S1_manifest.json"
# args['prediction_file'] = "/home/packerc/shared/machine_learning/data/info_files/RUA/RUA_S1/RUA_S1_new.csv"


if __name__ == "__main__":

    # Parse command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-manifest", type=str, required=True,
        help="Path to manifest file (.json)")
    parser.add_argument(
        "-prediction_file", type=str, required=True,
        help="Output file for the model to create predictions for (.csv)")
    parser.add_argument(
        "-max_images_per_capture", type=int, default=3,
        help="The maximum number of images per capture event (default 3)")

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

    print("Writing file to %s" % args['prediction_file'])
    with open(args['prediction_file'], 'w', newline='') as csvfile:
        csvwriter = csv.writer(csvfile, quotechar='', delimiter=',',
                               quoting=csv.QUOTE_ALL)
        # write header
        n_images = args['max_images_per_capture']
        image_cols = ['image%s' % x for x in range(1,  n_images + 1)]
        header = ['capture_id'] + image_cols
        csvwriter.writerow(header)

        # Write each capture event and the associated images
        for capture_id, mani_data in manifest.items():
            row_to_write = [capture_id]
            for image in mani_data['images']['original_images']:
                row_to_write.append(image)
            csvwriter.writerow(row_to_write)
