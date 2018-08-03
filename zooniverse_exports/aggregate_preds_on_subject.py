""" Aggregate predictions for individual images to Capture Events /
    Subject Ids to Assign prediction to Capture Events
"""
import csv
import json
import os
import argparse
from collections import Counter
from statistics import mean

from global_vars import label_mappings


# # subjects_path = 'D:\\Studium_GD\\Zooniverse\\SnapshotSafari\\data\\zooniverse_exports\\SER\\subjects.csv'
# manifest_root_path = 'D:\\Studium_GD\\Zooniverse\\SnapshotSafari\\data\\zooniverse\\Manifests\\SER\\'
# manifest_files = ['SER_S11_1_manifest_v1', 'SER_S11_2_manifest_v1']
# zooid_root_path = 'D:\\Studium_GD\\Zooniverse\\SnapshotSafari\\data\\zooniverse\\ZOOIDs\\SER\\'
# zooid_files = ['SER_S11_1_ZOOID_v0.csv', 'SER_S11_2_ZOOID_v0.csv']
# predictions_empty_path = 'D:\\Studium_GD\\Zooniverse\\SnapshotSafari\\data\\predictions\\empty_or_not\\SER\\SER_S11\\predictions_run_20180619.json'
# predictions_species_path = 'D:\\Studium_GD\\Zooniverse\\SnapshotSafari\\data\\predictions\\species\\SER\\SER_S11\\predictions_run_20180619.json'
# output_file = 'D:\\Studium_GD\\Zooniverse\\SnapshotSafari\\data\\zooniverse_exports\\SER\\SER_S11_predictions.json'
# label_mapping_path = 'D:\\Studium_GD\\Zooniverse\\SnapshotSafari\\data\\zooniverse_exports\\SER\\label_mapping.json'

subjects_path = 'D:\\Studium_GD\\Zooniverse\\SnapshotSafari\\data\\zooniverse_exports\\SER\\subjects.csv'
manifest_root_path = 'D:\\Studium_GD\\Zooniverse\\SnapshotSafari\\data\\zooniverse\\Manifests\\RUA\\'
manifest_files = ['RUA_S1_A1_manifest_v1']
zooid_root_path = 'D:\\Studium_GD\\Zooniverse\\SnapshotSafari\\data\\zooniverse\\ZOOIDs\\RUA\\'
zooid_files = ['RUA_S1_A1_ZOOID.csv']
predictions_empty_path = 'D:\\Studium_GD\\Zooniverse\\SnapshotSafari\\data\\predictions\\empty_or_not\\RUA\\RUA_S1\\evals_run_SER_fine_tune_20180627.json'
predictions_species_path = 'D:\\Studium_GD\\Zooniverse\\SnapshotSafari\\data\\predictions\\species\\RUA\\RUA_S1\\evals_run_originalSERmodel_20180626.json'
output_file = 'D:\\Studium_GD\\Zooniverse\\SnapshotSafari\\data\\zooniverse_exports\\RUA\\RUA_S1_predictions.json'
label_mapping_path = 'D:\\Studium_GD\\Zooniverse\\SnapshotSafari\\data\\zooniverse_exports\\RUA\\label_mapping.json'

# subjects_path = 'D:\\Studium_GD\\Zooniverse\\SnapshotSafari\\data\\zooniverse_exports\\SER\\subjects.csv'
# manifest_root_path = '/home/packerc/shared/zooniverse/Manifests/RUA/'
# manifest_files = ['RUA_S1_A1_manifest_v1']
# zooid_root_path = '/home/packerc/shared/zooniverse/ZOOIDs/RUA/'
# zooid_files = ['RUA_S1_A1_ZOOID.csv']
# predictions_empty_path = '/home/packerc/shared/machine_learning/data/predictions/empty_or_not/RUA/RUA_S1/predictions_run_SER_fine_tune_empty_val_20180708.json'
# predictions_species_path = '/home/packerc/shared/machine_learning/data/predictions/species/RUA/RUA_S1/predictions_run_SER_fine_tune_old_species_val_20180708.json'
# output_file = '/home/packerc/shared/machine_learning/data/zooniverse_exports/RUA/RUA_S1/RUA_S1_predictions_SER_fine_tuning_val.json'
# label_mapping_path = '/home/packerc/shared/machine_learning/data/zooniverse_exports/RUA/RUA_S1/label_mapping.json'
#


if __name__ == '__main__':

    # Parse command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("-manifest_root_path", type=str, required=True)
    parser.add_argument("-manifest_files", nargs='+', type=str, required=True)
    parser.add_argument("-zooid_root_path", type=str, required=True)
    parser.add_argument("-zooid_files", nargs='+', type=str, required=True)
    parser.add_argument("-predictions_empty_path", type=str, required=True)
    parser.add_argument("-predictions_species_path", type=str, required=True)
    parser.add_argument("-output_file", type=str, required=True)
    parser.add_argument("-label_mapping_path", type=str, required=True)
    parser.add_argument("-export_meta_data", action='store_true', default=False)
    parser.add_argument("-site_season_id", type=str, default='',
                        help="E.g. SER_S11")

    args = vars(parser.parse_args())

    manifest_root_path = args['manifest_root_path']
    manifest_files = args['manifest_files']
    zooid_root_path = args['zooid_root_path']
    zooid_files = args['zooid_files']
    predictions_empty_path = args['predictions_empty_path']
    predictions_species_path = args['predictions_species_path']
    output_file = args['output_file']
    label_mapping_path = args['label_mapping_path']

    # Read ZooID files
    anonym_to_im = dict()
    for file in zooid_files:
        full_path = os.path.join(zooid_root_path, file)
        with open(full_path, newline='') as csvfile:
            reader = csv.reader(csvfile, delimiter=',')
            for row_id, row in enumerate(reader):
                if row_id == 0:
                    header = row
                    name_to_id_mapping = {x: i for i, x in enumerate(header)}
                    continue
                else:
                    anonym_image_id = row[name_to_id_mapping['anonimname']]
                    image_name = row[name_to_id_mapping['imname']]
                    anonym_to_im[anonym_image_id] = image_name

    # Read predictions
    with open(predictions_empty_path, 'r') as f:
        predictions_empty = json.load(f)

    with open(predictions_species_path, 'r') as f:
        predictions_species = json.load(f)

    # Label Mapping
    with open(label_mapping_path, 'r') as f:
        label_mapping = json.load(f)
    # overwrite with old label mapping
    label_mapping = label_mappings['old_ser_label_mapping']
    label_mapping_empty = {'NOTHINGHERE': 0}

    # count mapping
    counts_map_to_numeric = label_mappings['counts_to_numeric']
    count_num_to_label = {v: k for k, v in counts_map_to_numeric.items()}

    # Read Manifest file
    anonym_to_subj = dict()
    for file in manifest_files:
        full_path = os.path.join(manifest_root_path, file)
        with open(full_path, newline='') as csvfile:
            reader = csv.reader(csvfile, delimiter=',')
            header = next(reader)
            col_mapping = {x: i for i, x in enumerate(header)}
            images = [x for x in col_mapping.keys() if 'Image' in x]
            for row_id, row in enumerate(reader):
                subject_id = row[col_mapping['zoosubjid']]
                site = row[col_mapping['site']]
                roll = row[col_mapping['roll']]
                capture = row[col_mapping['capture']]
                # unique capture id
                capture_id = '#'.join([args['site_season_id'],
                                       site,
                                       roll,
                                       capture])
                for img in images:
                    anonym_name = row[col_mapping[img]]
                    anonym_to_subj[anonym_name] = subject_id

    # Collect all predictions per Subject
    im_to_anonym = {v: k for k, v in anonym_to_im.items()}
    preds_all = dict()
    for _id, pred in predictions_empty.items():
        image_name = os.path.split(pred['path'])[-1]
        sub_id = anonym_to_subj[im_to_anonym[image_name]]
        if sub_id not in preds_all:
            preds_all[sub_id] = {'empty': [], 'species': []}
        preds_all[sub_id]['empty'].append(pred)

    for _id, pred in predictions_species.items():
        image_name = os.path.split(pred['path'])[-1]
        sub_id = anonym_to_subj[im_to_anonym[image_name]]
        if sub_id not in preds_all:
            preds_all[sub_id] = {'empty': [], 'species': []}
        preds_all[sub_id]['species'].append(pred)

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
            default_dict['empty'] = pred
            default_dict['empty_conf'] = conf
        # species and behaviors
        if 'species' in preds:
            pr, cf = extract_species_preds(preds['species'])
            pred, conf = aggregate_majority(pr, cf)
            default_dict['species'] = label_mapping_rev[pred]
            default_dict['species_conf'] = conf
            pr_d, cf_d = extract_behaviors(preds['species'])
            for behav in pr_d.keys():
                pr_b, cf_b = aggregate_binary_with_default0(pr_d[behav], cf_d[behav])
                default_dict[behav] = pr_b
                default_dict[behav + '_conf'] = cf_b
            # counts
            pr, cf = extract_counts(preds['species'])
            pred, conf = aggregate_majority(pr, cf)
            default_dict['count'] = count_num_to_label[pred]
            default_dict['count_conf'] = conf
        pred_aggregated[subject_id] = default_dict

    with open(output_file, 'w') as fp:
        json.dump(pred_aggregated, fp, indent=0)
