""" Create a csv with each line representing an image with its labels
    as aggregated from Zooniverse exports
    - this can be used to evaluate or train a machine learning model
"""
import csv
import json
import os
import random
import argparse

if __name__ == '__main__':

    # Parse command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("-zooid_path", type=str, required=True)
    parser.add_argument("-manifest_path", type=str, required=True)
    parser.add_argument("-zoo_exports_path", type=str, required=True)
    parser.add_argument("-ml_info_path", type=str, required=True)
    parser.add_argument("-manifest_files", nargs='+', type=str, required=True)
    parser.add_argument("-zooid_files", nargs='+', type=str, required=True)
    parser.add_argument("-season_id", type=str, required=True)

    args = vars(parser.parse_args())

    zooid_path = args['zooid_path']
    manifest_path = args['manifest_path']
    zoo_exports_path = args['zoo_exports_path']
    ml_info_output_path = args['ml_info_path']
    label_mapping_file = zoo_exports_path + 'label_mapping.json'
    manifest_files = args['manifest_files']
    zooid_files = args['zooid_files']
    s_id = args['season_id']

    input_files = {
        'input_file_aggregated': zoo_exports_path + 'classifications_aggregated.csv',
        'input_file_manifests': [manifest_path + x for x in manifest_files],
        'input_file_image_links': [zooid_path + x for x in zooid_files]
        }

    output_file = ml_info_output_path + s_id + '_all.csv'
    output_file_val_old = ml_info_output_path + s_id + '_all_val_old.csv'
    output_file_val = ml_info_output_path + s_id + '_all_val.csv'
    output_file_empty = ml_info_output_path + s_id + '_empty.csv'
    output_file_species = ml_info_output_path + s_id + '_species.csv'
    output_file_old_species = ml_info_output_path + s_id + '_old_species.csv'

    # input_files = {
    #     'input_file_aggregated': 'D:\\Studium_GD\\Zooniverse\\SnapshotSafari\\data\\zooniverse_exports\\SER\\classifications_aggregated.csv',
    #     'input_file_manifests': [
    #         'D:\\Studium_GD\\Zooniverse\\SnapshotSafari\\data\\zooniverse_upload_data\\SER_S11_1_manifest_v1',
    #         'D:\\Studium_GD\\Zooniverse\\SnapshotSafari\\data\\zooniverse_upload_data\\SER_S11_2_manifest_v1'],
    #     'input_file_image_links': [
    #         'D:\\Studium_GD\\Zooniverse\\SnapshotSafari\\data\\zooniverse_upload_data\\SER_S11_1_ZOOID.csv',
    #         'D:\\Studium_GD\\Zooniverse\\SnapshotSafari\\data\\zooniverse_upload_data\\SER_S11_2_ZOOID.csv']
    #         }
    #
    # output_file = 'D:\\Studium_GD\\Zooniverse\\SnapshotSafari\\data\\zooniverse_exports\\SER\\ml_file.csv'
    # output_file_empty = 'D:\\Studium_GD\\Zooniverse\\SnapshotSafari\\data\\zooniverse_exports\\SER\\ml_file_empty.csv'
    # output_file_species = 'D:\\Studium_GD\\Zooniverse\\SnapshotSafari\\data\\zooniverse_exports\\SER\\ml_file_species.csv'
    # output_file_old_species = 'D:\\Studium_GD\\Zooniverse\\SnapshotSafari\\data\\zooniverse_exports\\SER\\ml_file_old_species.csv'
    # label_mapping_file = 'D:\\Studium_GD\\Zooniverse\\SnapshotSafari\\data\\zooniverse_exports\\SER\\label_mapping.json'

    def add_postfix_to_path(file_path, postfix):
        """ Add a Postfix to the Filename """
        fname = os.path.split(file_path)[1]
        path = os.path.split(file_path)[0]
        fname_new = fname.split('.')[0] + '_' + postfix + '.' + fname.split('.')[1]
        new_path = os.path.join(path, fname_new)
        return new_path

    output_file_species_train = add_postfix_to_path(output_file_species, 'train')
    output_file_species_val = add_postfix_to_path(output_file_species, 'val')
    output_file_empty_train = add_postfix_to_path(output_file_empty, 'train')
    output_file_empty_val = add_postfix_to_path(output_file_empty, 'val')
    output_file_old_species_train = add_postfix_to_path(output_file_old_species, 'train')
    output_file_old_species_val = add_postfix_to_path(output_file_old_species, 'val')

    # Read manifests and create Image ID to Subject ID mapping
    image_id_to_sub = dict()
    for file in input_files['input_file_manifests']:
        with open(file, newline='') as csvfile:
            reader = csv.reader(csvfile, delimiter=',')
            for row_id, row in enumerate(reader):
                if row_id == 0:
                    header = row
                    name_to_id_mapping = {x: i for i, x in enumerate(header)}
                    continue
                else:
                    # Skip unsuccessful uploads
                    if not row[name_to_id_mapping['uploadstatus']] == 'UC':
                        continue
                    subject_id = row[name_to_id_mapping['zoosubjid']]
                    image_cols = [v for k, v in name_to_id_mapping.items() if 'Image' in k]
                    for image_col in image_cols:
                        # Do not read invalid images
                        if not row[image_col] in ['NA', 'IN', 'CR']:
                            if row[image_col] in image_id_to_sub:
                                print("Duplicate Image ID: %s Subject: %s"
                                      % (row[image_col], subject_id))
                            image_id_to_sub[row[image_col]] = subject_id

    # Read ZOOID files to map image paths to zoo ids
    zooid_to_img_path = dict()
    for file in input_files['input_file_image_links']:
        with open(file, newline='') as csvfile:
            reader = csv.reader(csvfile, delimiter=',')
            for row_id, row in enumerate(reader):
                if row_id == 0:
                    header = row
                    name_to_id_mapping = {x: i for i, x in enumerate(header)}
                    continue
                else:
                    zoo_img_id = row[name_to_id_mapping['anonimname']]
                    # img_path = row[name_to_id_mapping['absimpath']]
                    img_path = row[name_to_id_mapping['path']]
                    if zoo_img_id in zooid_to_img_path:
                        print("Duplicate Image ID: %s Path: %s"
                              % (zoo_img_id, img_path))
                    zooid_to_img_path[zoo_img_id] = img_path

    # Read aggregated subject id file
    subs = dict()
    dubs = list()
    with open(input_files['input_file_aggregated'], newline='') as csvfile:
        reader = csv.reader(csvfile, delimiter=',')
        for row_id, row in enumerate(reader):
            if row_id == 0:
                header = row
                name_to_id_mapping = {x: i for i, x in enumerate(header)}
                id_to_name_mapping = {i: x for i, x in enumerate(header)}
                continue
            else:
                #row_data = [row[k] for k, v in id_to_name_mapping.items()]
                #subs[row[name_to_id_mapping['subject_id']]] = row_data
                row_data = {v:row[k] for k, v in id_to_name_mapping.items()}
                sub_id = row[name_to_id_mapping['subject_id']]
                if sub_id in subs:
                    dubs.append(sub_id)
                subs[sub_id] = row_data
    # remove subjects with multiple species duplicates
    for dub in dubs:
        subs.pop(dub, None)

    # Read Label Mapping
    with open(label_mapping_file, 'r') as f:
        label_mapping = json.load(f)

    map_id_to_names= {
        0:'Aardvark',1:'Aardwolf',2:'Baboon',3:'Bateared Fox',4:'Buffalo',
        5:'Bushbuck',6:'Caracal',7:'Cheetah',8:'Civet',9:'Dikdik',10:'Eland',
        11:'Elephant',12:'Gazelle Grants',13:'Gazelle Thomsons',14:'Genet',
        15:'Giraffe',16:'Guineafowl',
        17:'Hare',18:'Hartebeest',19:'Hippopotamus',20:'Honeybadger'
        ,21:'Human',
        22:'Hyena Spotted',23:'Hyena Striped',24:'Impala',25:'Jackal',
        26:'Koribustard',
        27:'Leopard',28:'Lion Female',29:'Lion Male',30:'Mongoose',
        31:'Ostrich', 32:'Other Bird',33:'Porcupine',34:'Reedbuck',
        35:'Reptiles',
        36:'Rhinoceros',37:'Rodents',38:'Secretary Bird',39:'Serval',
        40:'Topi',41:'Vervet Monkey',42:'Warthog',43:'Waterbuck',
        44:'Wild Cat',45:'Wildebeest',46:'Zebra',47:'Zorilla'}

    map_names_to_id = {v: k for k, v in map_id_to_names.items()}

    map_names_to_zooniverse_names = {
            k: k.upper().replace(' ', '')
            for k in map_names_to_id.keys()}
    map_names_to_zooniverse_names['Other Bird'] = 'BIRDOTHER'
    map_names_to_zooniverse_names['Vervet Monkey'] = 'MONKEYVERVET'
    map_zoo_to_names = {v: k for k, v in map_names_to_zooniverse_names.items()}
    label_order = ['count', 'standing', 'resting', 'moving', 'eating',
                   'interacting', 'young_present']
    map_label_to_row_id={'count': 3, 'standing': 4, 'resting': 5, 'moving': 6,
                         'eating': 7, 'interacting': 8, 'young_present': 9}
    counts_mapping = {1150: 11, 0: 1}
    species_not_ml = ['Fire', 'VULTURE', 'HYENABROWN', 'DUIKER', 'BAT',
                      'CATTLE', 'KUDU', 'SABLE', 'WILDDOG', 'BUSHPIG',
                      'INSECTSPIDER']

    map_names_to_id2 = {map_names_to_zooniverse_names[k]: v for k, v in map_names_to_id.items()}


    # OLD Season 1-6 SER Mapping
    map_species_zoonames_to_id_old = {
     'AARDVARK': 0, 'AARDWOLF': 1, 'BABOON': 2,
     'BATEAREDFOX': 3, 'BUFFALO': 4, 'BUSHBUCK': 5, 'CARACAL': 6, 'CHEETAH': 7,
     'CIVET': 8, 'DIKDIK': 9, 'ELAND': 10, 'ELEPHANT': 11,
     'GAZELLEGRANTS': 12, 'GAZELLETHOMSONS': 13, 'GENET': 14, 'GIRAFFE': 15,
     'GUINEAFOWL': 16, 'HARE': 17, 'HARTEBEEST': 18, 'HIPPOPOTAMUS': 19,
     'HONEYBADGER': 20, 'HUMAN': 21, 'HYENASPOTTED': 22, 'HYENASTRIPED': 23,
     'IMPALA': 24, 'JACKAL': 25, 'KORIBUSTARD': 26, 'LEOPARD': 27,
     'LIONFEMALE': 28, 'LIONMALE': 29, 'MONGOOSE': 30, 'OSTRICH': 31,
     'BIRDOTHER': 32, 'PORCUPINE': 33, 'REEDBUCK': 34, 'REPTILES': 35,
     'RHINOCEROS': 36, 'RODENTS': 37, 'SECRETARYBIRD': 38, 'SERVAL': 39,
     'TOPI': 40, 'MONKEYVERVET': 41, 'WARTHOG': 42, 'WATERBUCK': 43,
     'WILDCAT': 44, 'WILDEBEEST': 45, 'ZEBRA': 46, 'ZORILLA': 47}

    map_id_to_species_zoonames_old = {
        v: k for k, v in map_species_zoonames_to_id_old.items()}

    map_empty_zoonames_to_id_old = {'NOTHINGHERE': 0}
    map_id_to_empty_zoonames_old = {0: 'NOTHINGHERE'}

    # NEW Snapshot Safari Mapping
    map_empty_species_old = {
        k: 1 for k in map_species_zoonames_to_id_old.keys()}
    map_empty_species = {k: 1 for k in label_mapping.keys()}
    map_empty_species_all = {**map_empty_species, **map_empty_species_old}
    map_empty_to_id = {'NOTHINGHERE': 0, **map_empty_species_all}

    def _create_ml_record(image_path, label_data, behav_attrs,
                          label_mapping, label_order, counts_mapping):
        """ Create a ML Record """
        if label_data['species'] in label_mapping:
            species_num = label_mapping[label_data['species']]
            count_val = behav_attrs[label_order.index('count')]
            if count_val in counts_mapping:
                behav_attrs[label_order.index('count')] = \
                    counts_mapping[count_val]
            ml_row = [image_path, species_num] + behav_attrs
            return ml_row
        else:
            return None

    # Merge all files
    ml_data_d = dict()
    n_not_found = 0
    for zoo_id, subject_id in image_id_to_sub.items():
        if subject_id not in subs:
            print("Subject %s not in aggregated export" % subject_id)
            n_not_found += 1
            continue
        image_path = zooid_to_img_path[zoo_id]
        label_data = subs[subject_id]
        behav_attrs = [int(label_data[x]) for x in label_order]
        # Create ML record (s)
        ml_species = _create_ml_record(
            image_path, label_data, behav_attrs,
            label_mapping, label_order, counts_mapping)
        ml_empty = _create_ml_record(
            image_path, label_data, behav_attrs,
            map_empty_to_id, label_order, counts_mapping)
        ml_old_species = _create_ml_record(
            image_path, label_data, behav_attrs,
            map_species_zoonames_to_id_old, label_order, counts_mapping)
        row_dict = dict()
        row_dict['ml_species'] = ml_species
        row_dict['ml_empty'] = ml_empty
        row_dict['ml_old_species'] = ml_old_species
        row_dict['label_data'] = label_data
        row_dict['behav_attrs'] = behav_attrs
        row_dict['subject_id'] = subject_id
        unique_id = zoo_id + '#' + subject_id
        ml_data_d[unique_id] = row_dict

    print("%s subjects not found in aggregated export" % n_not_found)
    ml_data_d[list(ml_data_d.keys())[0]]

    # Check Counts
    from collections import Counter
    counts = list()
    for rr in ml_data_d.values():
        if rr['ml_species'] is not None:
            counts.append(rr['ml_species'][2])
    Counter(counts)

    def export_ml_files(ml_data_d):
        """ Export ML data """
        # Export Empty ML File
        with open(output_file_empty, "w", newline='') as outs:
            csv_writer = csv.writer(outs, delimiter=',')
            print("Writing file to %s" % output_file_empty)
            for ml_data in ml_data_d.values():
                if ml_data['ml_empty'] is not None:
                    csv_writer.writerow(ml_data['ml_empty'][0:2])

        # Export Species OLD
        with open(output_file_old_species, "w", newline='') as outs:
            csv_writer = csv.writer(outs, delimiter=',')
            print("Writing file to %s" % output_file_old_species)
            for ml_data in ml_data_d.values():
                if ml_data['ml_old_species'] is not None:
                    csv_writer.writerow(ml_data['ml_old_species'])

        # Export Species
        with open(output_file_species, "w", newline='') as outs:
            csv_writer = csv.writer(outs, delimiter=',')
            print("Writing file to %s" % output_file_species)
            for ml_data in ml_data_d.values():
                if ml_data['ml_species'] is not None:
                    csv_writer.writerow(ml_data['ml_species'])

        # Export Splitted Species
        all_subject_ids = set()
        for ml_data in ml_data_d.values():
            if ml_data['ml_species'] is not None:
                all_subject_ids.add(ml_data['subject_id'])

        # sample into train / val
        random.seed(123)
        n_total = len(all_subject_ids)
        n_val = round(n_total*0.2)
        n_train = n_total - n_val
        train_ids = random.sample(all_subject_ids, n_train)

        # Export Train Species
        with open(output_file_species_train, "w", newline='') as outs:
            csv_writer = csv.writer(outs, delimiter=',')
            print("Writing file to %s" % output_file_species_train)
            for ml_data in ml_data_d.values():
                if ml_data['ml_species'] is not None:
                    if ml_data['subject_id'] in train_ids:
                        csv_writer.writerow(ml_data['ml_species'])

        # Export Val Species
        with open(output_file_species_val, "w", newline='') as outs:
            csv_writer = csv.writer(outs, delimiter=',')
            print("Writing file to %s" % output_file_species_val)
            for ml_data in ml_data_d.values():
                if ml_data['ml_species'] is not None:
                    if ml_data['subject_id'] not in train_ids:
                        csv_writer.writerow(ml_data['ml_species'])

        # Export Train Species OLD
        with open(output_file_old_species_train, "w", newline='') as outs:
            csv_writer = csv.writer(outs, delimiter=',')
            print("Writing file to %s" % output_file_old_species_train)
            for ml_data in ml_data_d.values():
                if ml_data['ml_old_species'] is not None:
                    if ml_data['subject_id'] in train_ids:
                        csv_writer.writerow(ml_data['ml_old_species'])

        # Export Val Species OLD
        with open(output_file_old_species_val, "w", newline='') as outs:
            csv_writer = csv.writer(outs, delimiter=',')
            print("Writing file to %s" % output_file_old_species_val)
            for ml_data in ml_data_d.values():
                if ml_data['ml_old_species'] is not None:
                    if ml_data['subject_id'] not in train_ids:
                        csv_writer.writerow(ml_data['ml_old_species'])

        # Export Splitted Empty
        all_subject_ids = set()
        empty_subject_ids = set()
        species_subject_ids = set()
        for ml_data in ml_data_d.values():
            if ml_data['ml_empty'] is not None:
                if ml_data['ml_empty'][1] == 0:
                    empty_subject_ids.add(ml_data['subject_id'])
                else:
                    species_subject_ids.add(ml_data['subject_id'])
                all_subject_ids.add(ml_data['subject_id'])

        # sample into train / val
        balanced_sample_size = min([len(empty_subject_ids),
                                    len(species_subject_ids)])

        train_size_fraction = 0.8
        balanced_sample_size = int(balanced_sample_size * train_size_fraction)

        random.seed(123)
        train_ids_empty = random.sample(empty_subject_ids,
                                        balanced_sample_size)
        random.seed(123)
        train_ids_species = random.sample(species_subject_ids,
                                          balanced_sample_size)
        train_ids = set(train_ids_empty + train_ids_species)

        # Export Train EMPTY
        with open(output_file_empty_train, "w", newline='') as outs:
            csv_writer = csv.writer(outs, delimiter=',')
            print("Writing file to %s" % output_file_empty_train)
            for ml_data in ml_data_d.values():
                if ml_data['ml_empty'] is not None:
                    if ml_data['subject_id'] in train_ids:
                        csv_writer.writerow(ml_data['ml_empty'][0:2])

        # Export Val EMPTY
        with open(output_file_empty_val, "w", newline='') as outs:
            csv_writer = csv.writer(outs, delimiter=',')
            print("Writing file to %s" % output_file_empty_val)
            for ml_data in ml_data_d.values():
                if ml_data['ml_empty'] is not None:
                    if ml_data['subject_id'] not in train_ids:
                        csv_writer.writerow(ml_data['ml_empty'][0:2])

        # Export consolidated Val Data for Simulations (new species)
        val_records = list()
        with open(output_file_empty_val, "r", newline='') as f:
            for line in f:
                val_records.append(line)
        with open(output_file_species_val, "r", newline='') as f:
            for line in f:
                val_records.append(line)

        with open(output_file_val, "w", newline='') as outs:
            csv_writer = csv.writer(outs, delimiter=',')
            print("Writing file to %s" % output_file_val)
            for val_record in val_records:
                csv_writer.writerow(val_record)

        # Export consolidated Val Data for Simulations (old species)
        val_records = list()
        with open(output_file_empty_val, "r", newline='') as f:
            for line in f:
                val_records.append(line)
        with open(output_file_old_species_val, "r", newline='') as f:
            for line in f:
                val_records.append(line)

        with open(output_file_val_old, "w", newline='') as outs:
            csv_writer = csv.writer(outs, delimiter=',')
            print("Writing file to %s" % output_file_val_old)
            for val_record in val_records:
                csv_writer.writerow(val_record)

    export_ml_files(ml_data_d)
