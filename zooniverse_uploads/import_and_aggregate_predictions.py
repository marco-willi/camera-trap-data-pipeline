""" Import Model Predictions and Aggregate on Subject Level """
import json
import os
import argparse
from collections import Counter
from statistics import mean

# # For Testing
# args = dict()
# args['manifest'] = "/home/packerc/shared/zooniverse/Manifests/RUA/RUA_S1_manifest.json"
# args['empty_predictions'] = '/home/packerc/shared/machine_learning/data/predictions/empty_or_not/RUA/RUA_S1/predictions_run_manifest_20180628.json'
# args['species_predictions'] = '/home/packerc/shared/machine_learning/data/predictions/species/RUA/RUA_S1/predictions_run_manifest_20180628.json'
# args['output_file'] = "/home/packerc/shared/zooniverse/Manifests/RUA/RUA_S1_preds_aggregated.json"

if __name__ == "__main__":

    # Parse command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-manifest", type=str, required=True,
        help="Path to manifest file (.json)")
    parser.add_argument(
        "-empty_predictions", type=str, required=True,
        help="Predictions from the empty model (.json)")

    parser.add_argument(
        "-species_predictions", type=str, required=True,
        help="Predictions from the species model (.json)")

    parser.add_argument(
        "-output_file", type=str, required=True,
        help="Output file to write aggregated predictions to (.json)")

    args = vars(parser.parse_args())

    for k, v in args.items():
        print("Argument %s: %s" % (k, v))

    # Check Inputs
    if not os.path.exists(args['manifest']):
        raise FileNotFoundError("manifest: %s not found" %
                                args['manifest'])

    if not os.path.exists(args['empty_predictions']):
        raise FileNotFoundError("empty_predictions: %s not found" %
                                args['empty_predictions'])

    if not os.path.exists(args['species_predictions']):
        raise FileNotFoundError("species_predictions: %s not found" %
                                args['species_predictions'])

    # overwrite with old label mapping
    label_mapping = {
         'AARDVARK': 0, 'AARDWOLF': 1, 'BABOON': 2,
         'BATEAREDFOX': 3, 'BUFFALO': 4, 'BUSHBUCK': 5, 'CARACAL': 6,
         'CHEETAH': 7,
         'CIVET': 8, 'DIKDIK': 9, 'ELAND': 10, 'ELEPHANT': 11,
         'GAZELLEGRANTS': 12, 'GAZELLETHOMSONS': 13, 'GENET': 14,
         'GIRAFFE': 15,
         'GUINEAFOWL': 16, 'HARE': 17, 'HARTEBEEST': 18, 'HIPPOPOTAMUS': 19,
         'HONEYBADGER': 20, 'HUMAN': 21, 'HYENASPOTTED': 22,
         'HYENASTRIPED': 23,
         'IMPALA': 24, 'JACKAL': 25, 'KORIBUSTARD': 26, 'LEOPARD': 27,
         'LIONFEMALE': 28, 'LIONMALE': 29, 'MONGOOSE': 30, 'OSTRICH': 31,
         'BIRDOTHER': 32, 'PORCUPINE': 33, 'REEDBUCK': 34, 'REPTILES': 35,
         'RHINOCEROS': 36, 'RODENTS': 37, 'SECRETARYBIRD': 38, 'SERVAL': 39,
         'TOPI': 40, 'MONKEYVERVET': 41, 'WARTHOG': 42, 'WATERBUCK': 43,
         'WILDCAT': 44, 'WILDEBEEST': 45, 'ZEBRA': 46, 'ZORILLA': 47}

    label_mapping_empty = {'NOTHINGHERE': 0, 'SOMETHINGHERE': 1}
    empty_num_to_label = {v: k for k, v in label_mapping_empty.items()}

    # count mapping
    counts_map_to_numeric = {"1": 0, "2": 1, "3": 2, "4": 3,
                             "5": 4, "6": 5, "7": 6, "8": 7, "9": 8,
                             "10": 9, "1150": 10, "51": 11}
    count_num_to_label = {v: k for k, v in counts_map_to_numeric.items()}

    # import manifest
    with open(args['manifest'], 'r') as f:
        mani = json.load(f)

    # import species and empty predictions
    with open(args['empty_predictions'], 'r') as f:
        predictions_empty = json.load(f)

    with open(args['species_predictions'], 'r') as f:
        predictions_species = json.load(f)

    # Create mapping: image name to subject id
    img_to_capture_id_map = dict()
    for k, v in mani.items():
        image_paths = v['images']['original_images']
        for image_path in image_paths:
            image_name = os.path.split(image_path)[-1]
            img_to_capture_id_map[image_name] = k

    # Collect all predictions per Capture ID
    preds_all = dict()
    for pred in predictions_empty.values():
        image_name = os.path.split(pred['path'])[-1]
        # Skip if predicted image is not in Manifest
        if image_name not in img_to_capture_id_map:
            continue
        capture_id = img_to_capture_id_map[image_name]
        if capture_id not in preds_all:
            preds_all[capture_id] = {'empty': [], 'species': []}
        preds_all[capture_id]['empty'].append(pred)

    for pred in predictions_species.values():
        image_name = os.path.split(pred['path'])[-1]
        # Skip if predicted image is not in Manifest
        if image_name not in img_to_capture_id_map:
            continue
        capture_id = img_to_capture_id_map[image_name]
        if capture_id not in preds_all:
            preds_all[capture_id] = {'empty': [], 'species': []}
        preds_all[capture_id]['species'].append(pred)

    # Aggregate Machine Predictions
    def extract_empty_preds(preds):
        """ Extract Empty Preds """
        class_preds = list()
        class_confs = list()
        for pred in preds:
            class_preds.append(pred['top_n_pred'][0])
            class_confs.append(pred['top_n_conf'][0])
        return class_preds, class_confs

    def extract_species_preds(preds):
        """ Extract Species Preds """
        species_preds = list()
        species_confs = list()
        for pred in preds:
            species_preds.append(pred['top_n_pred'][0])
            species_confs.append(pred['top_n_conf'][0])
        return species_preds, species_confs

    def extract_behaviors(preds):
        """ Extract Behavior Preds """
        behaviors = ['standing',  'moving', 'eating', 'interacting',
                     'resting', 'young_present']
        behav_preds = {k: [] for k in behaviors}
        behav_confs = {k: [] for k in behaviors}

        for pred in preds:
            for behav in behaviors:
                behav_preds[behav].append(pred['top_pred_' + behav])
                behav_confs[behav].append(pred['top_conf_' + behav])
        return behav_preds, behav_confs

    def extract_counts(preds):
        """ Extract Count Preds """
        count_preds = list()
        count_confs = list()
        for pred in preds:
            count_preds.append(pred['top_n_pred_count'][0])
            count_confs.append(pred['top_n_conf_count'][0])
        return count_preds, count_confs

    def aggregate_majority(preds, confs):
        """ Aggregate Predictions
            - find most frequent prediction
            - calculate mean confidence of most frequent prediction
        """
        ranked = Counter(preds)
        pred = ranked.most_common(1)[0][0]
        confs_pred = [c for p, c in zip(preds, confs) if p == pred]
        conf = mean(confs_pred)
        return pred, conf

    def aggregate_binary_with_default0(preds, confs, threshold=0.5):
        """ Aggregate Binary predictions with default value
            - if default is zero, evidence of 1 in an of the predictions is
              enough to override default predictions
        """
        non_default = [c for p, c in zip(preds, confs) if p is not 0]
        if len(non_default) > 0:
            max_conf_non_default = max(non_default)
            if max_conf_non_default > threshold:
                return 1, max_conf_non_default
            else:
                return 0, 1-max_conf_non_default
        else:
            return 0, mean(confs)

    # Extract and aggregate all Predictions
    pred_aggregated = dict()
    label_mapping_rev = {v: k for k, v in label_mapping.items()}
    for subject_id, preds in preds_all.items():
        behaviors = ['standing',  'moving', 'eating', 'interacting',
                     'resting', 'young_present']
        labels = ['empty', 'species'] + behaviors
        default_dict = {**{x: 0 for x in labels},
                        **{x + '_conf': 0 for x in labels}}
        # Empty
        if 'empty' in preds:
            pr, cf = extract_empty_preds(preds['empty'])
            pred, conf = aggregate_binary_with_default0(pr, cf)
            default_dict['empty'] = empty_num_to_label[pred]
            default_dict['empty_conf'] = conf
        # species and behaviors
        if 'species' in preds:
            pr, cf = extract_species_preds(preds['species'])
            pred, conf = aggregate_majority(pr, cf)
            default_dict['species'] = label_mapping_rev[pred]
            default_dict['species_conf'] = conf
            pr_d, cf_d = extract_behaviors(preds['species'])
            for behav in pr_d.keys():
                pr_b, cf_b = aggregate_binary_with_default0(pr_d[behav],
                                                            cf_d[behav])
                default_dict[behav] = pr_b
                default_dict[behav + '_conf'] = cf_b
            # counts
            pr, cf = extract_counts(preds['species'])
            pred, conf = aggregate_majority(pr, cf)
            default_dict['count'] = count_num_to_label[pred]
            default_dict['count_conf'] = conf
        pred_aggregated[subject_id] = default_dict

    with open(args['output_file'], 'w') as fp:
        json.dump(pred_aggregated, fp, indent=0)
