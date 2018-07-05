""" Remove specific records / capture events from the Manifest
    - for example: already uploaded and processed records
"""
import csv
import json
import argparse
import os

# # For Testing
# args = dict()
# args['manifest'] = "/home/packerc/shared/zooniverse/Manifests/RUA/RUA_S1_manifest.json"
# args['old_manifest_to_remove'] = '/home/packerc/shared/zooniverse/Manifests/RUA/RUA_S1_A1_manifest_v1'
# args['season'] = 'RUA_S1'

if __name__ == "__main__":

    # Parse command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-manifest", type=str, required=True,
        help="Path to manifest file (.json), will be overwritten")

    parser.add_argument(
        "-old_manifest_to_remove", type=str, required=True,
        help="Old manifest (must contain 'site', 'roll', 'capture') in file \
             (*v1 file)")

    parser.add_argument(
        "-season", type=str, required=True,
        help="Season prefix, e.g. 'RUA_S1'")

    args = vars(parser.parse_args())

    for k, v in args.items():
        print("Argument %s: %s" % (k, v))

    # Check Inputs
    if not os.path.exists(args['manifest']):
        raise FileNotFoundError("manifest: %s not found" %
                                args['manifest'])

    # read old manifest (csv)
    processed_capture_ids = set()
    with open(args['old_manifest_to_remove'], "r", encoding="utf-8") as ins:
        csv_reader = csv.reader(ins, delimiter=',')
        for _id, line in enumerate(csv_reader):
            if _id == 0:
                row_name_to_id_mapper = {x: i for i, x in enumerate(line)}
                row_id_to_name_mapper = {i: x for i, x in enumerate(line)}
            else:
                site = line[row_name_to_id_mapper['site']]
                roll = line[row_name_to_id_mapper['roll']]
                capture = line[row_name_to_id_mapper['capture']]
                capture_id = '#'.join([args['season'], site, roll, capture])
                processed_capture_ids.add(capture_id)

    n_records_to_remove = len(processed_capture_ids)

    # read current manifest
    with open(args['manifest'], 'r') as f:
        manifest = json.load(f)

    n_records_before = len(manifest.keys())

    # remove records
    for id_to_remove in processed_capture_ids:
        _ = manifest.pop(id_to_remove, None)

    n_records_after = len(manifest.keys())

    print("Records to remove: %s - Actually removed: %s" %
          (n_records_to_remove, n_records_before - n_records_after))

    # Export Manifest
    with open(args['manifest'], 'w') as outfile:
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
