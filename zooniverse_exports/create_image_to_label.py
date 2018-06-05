""" Create a csv with each line representing an image with its labels
    as aggregated from Zooniverse exports
    - this can be used to evaluate or train a machine learning model
"""
import csv
from utils import print_progress

if __name__ == '__main__':

    zooid_path = '/home/packerc/shared/zooniverse/ZOOIDs/SER/'
    manifest_path = '/home/packerc/shared/zooniverse/Manifests/SER/'
    zoo_exports_path = '/home/packerc/shared/machine_learning/will5448/data/zooniverse_exports/SER/'
    ml_info_output_path = '/home/packerc/shared/machine_learning/data/info_files/SER/'

    input_files = {
        'input_file_aggregated': zoo_exports_path + 'classifications_aggregated.csv',
        'input_file_manifests': [manifest_path + 'SER_S11_1_manifest_v1',
                                 manifest_path + 'SER_S11_2_manifest_v1'],
        'input_file_image_links': [zooid_path + 'SER_S11_1_ZOOID.csv',
                                   zooid_path + 'SER_S11_2_ZOOID.csv']
            }

    output_file = ml_info_output_path + 'SER_S11_all.csv'
    output_file_empty = ml_info_output_path + 'SER_S11_empty.csv'
    output_file_species = ml_info_output_path + 'SER_S11_species.csv'


    # input_files = {
    #     'input_file_aggregated': 'D:\\Studium_GD\\Zooniverse\\SnapshotSafari\\data\\zooniverse_exports\\classifications_aggregated.csv',
    #     'input_file_manifests': [
    #         'D:\\Studium_GD\\Zooniverse\\SnapshotSafari\\data\\zooniverse_upload_data\\SER_S11_1_manifest_v1',
    #         'D:\\Studium_GD\\Zooniverse\\SnapshotSafari\\data\\zooniverse_upload_data\\SER_S11_2_manifest_v1'],
    #     'input_file_image_links': [
    #         'D:\\Studium_GD\\Zooniverse\\SnapshotSafari\\data\\zooniverse_upload_data\\SER_S11_1_ZOOID.csv',
    #         'D:\\Studium_GD\\Zooniverse\\SnapshotSafari\\data\\zooniverse_upload_data\\SER_S11_2_ZOOID.csv']
    #         }
    #
    # output_file = 'D:\\Studium_GD\\Zooniverse\\SnapshotSafari\\data\\zooniverse_exports\\ml_file.csv'
    # output_file_empty = 'D:\\Studium_GD\\Zooniverse\\SnapshotSafari\\data\\zooniverse_exports\\ml_file_empty.csv'
    # output_file_species = 'D:\\Studium_GD\\Zooniverse\\SnapshotSafari\\data\\zooniverse_exports\\ml_file_species.csv'

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
                subs[row[name_to_id_mapping['subject_id']]] = row_data


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
        31:'Ostrich',
        32:'Other Bird',33:'Porcupine',34:'Reedbuck',35:'Reptiles',
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

    species_not_ml = ['Fire', 'VULTURE', 'HYENABROWN', 'DUIKER', 'BAT']

    # Merge all files
    ml_data = list()
    for zoo_id, subject_id in image_id_to_sub.items():
        image_path = zooid_to_img_path[zoo_id]
        label_data = subs[subject_id]
        behav_attrs = [int(label_data[x]) for x in label_order]
        # Create ML record
        if label_data['species'] in ['NOTHINGHERE',  'Fire']:
            empty = 0
            species_num = None
        else:
            empty = 1
            if label_data['species'] in species_not_ml:
                species_num = None
            else:
                species = map_zoo_to_names[label_data['species']]
                species_num = map_names_to_id[species]
            # Map counts to eligible values
            count_val = behav_attrs[label_order.index('count')]
            if count_val in counts_mapping:
                behav_attrs[label_order.index('count')] = counts_mapping[count_val]
        row_ml = [image_path, empty, species_num] + behav_attrs
        ml_data.append(row_ml)


    # Check Counts
    from collections import Counter
    counts = list()
    for rr in ml_data:
        counts.append(rr[3])
    Counter(counts)

    # Export File
    with open(output_file, "w", newline='') as outs:
        csv_writer = csv.writer(outs, delimiter=',')
        print("Writing file to %s" % output_file)
        tot = len(ml_data)
        for i, line in enumerate(ml_data):
            print_progress(i, tot)
            csv_writer.writerow(line)


    with open(output_file_empty, "w", newline='') as outs:
        csv_writer = csv.writer(outs, delimiter=',')
        print("Writing file to %s" % output_file_empty)
        tot = len(ml_data)
        for i, line in enumerate(ml_data):
            print_progress(i, tot)
            csv_writer.writerow(line[0:2])

    with open(output_file_species, "w", newline='') as outs:
        csv_writer = csv.writer(outs, delimiter=',')
        print("Writing file to %s" % output_file_species)
        tot = len(ml_data)
        for i, line in enumerate(ml_data):
            print_progress(i, tot)
            if line[2] is not None:
                csv_writer.writerow(line)
