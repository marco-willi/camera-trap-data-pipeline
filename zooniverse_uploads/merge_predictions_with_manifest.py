""" Integrate Aggregated Predictions with Manifest """
import json
import os
import argparse

# # For Testing
# args = dict()
# args['manifest'] = "/home/packerc/shared/zooniverse/Manifests/RUA/RUA_S1_manifest.json"
# args['predictions'] = "/home/packerc/shared/zooniverse/Manifests/RUA/RUA_S1_preds_aggregated.json"
# args['output_file'] = "/home/packerc/shared/zooniverse/Manifests/RUA/RUA_S1_manifest1.json"

if __name__ == "__main__":

    # Parse command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-manifest", type=str, required=True,
        help="Path to manifest file (.json)")
    parser.add_argument(
        "-predictions", type=str, required=True,
        help="Aggregated predictions (.json)")

    parser.add_argument(
        "-output_file", type=str, required=True,
        help="Output file to write new manifest to (.json)")

    args = vars(parser.parse_args())

    for k, v in args.items():
        print("Argument %s: %s" % (k, v))

    # Check Inputs
    if not os.path.exists(args['manifest']):
        raise FileNotFoundError("manifest: %s not found" %
                                args['manifest'])

    # Check Inputs
    if not os.path.exists(args['predictions']):
        raise FileNotFoundError("predictions: %s not found" %
                                args['predictions'])

    # import manifest
    with open(args['manifest'], 'r') as f:
        mani = json.load(f)

    # import predictions
    with open(args['predictions'], 'r') as f:
        preds = json.load(f)

    # Merge predictions with manifest
    for capture_id, data in mani.items():
        # get predictions
        if capture_id in preds:
            current_preds = preds[capture_id]
            # add elements to subject metadata
            meta_data = data['upload_metadata']
            for pred_key, pred_value in current_preds.items():
                meta_key = '#machine_prediction_%s' % pred_key
                meta_data[meta_key] = pred_value
            # adjust status
            data['info']['machine_learning'] = True
        else:
            data['info']['machine_learning'] = False

    # Export Manifest
    with open(args['output_file'], 'w') as outfile:
        first_row = True
        for _id, values in mani.items():
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
