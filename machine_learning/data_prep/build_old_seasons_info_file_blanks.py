""" Build an info file for model training using data from seasons 1-8 """
import os
import csv
import random


def correct_image_name(name):
    """ change image name
    OLD: S1/G12/G12_R1/PICT3981.JPG
    NEW: S1/G12/G12_R1/S1_G12_R1_PICT3981.JPG

    OLD: S8/O09/O09_R3/S8_O09_R3_S8_O09_R3_IMAG9279.JPG
    NEW: S8/O09/O09_R3/S8_O09_R3_S8_O09_R3_IMAG9279.JPG
    """
    if '/' not in name:
        return name
    name_splits = name.split('/')
    if '_' in name_splits[-1]:
        return name
    path = '/'.join(name_splits[0:-1])
    file_name_new = '_'.join([name_splits[0], name_splits[2], name_splits[3]])
    return path + '/' + file_name_new


if __name__ == '__main__':

    # Parameters
    output_file = '/home/packerc/shared/machine_learning/data/info_files/SER/blanks_prev.csv'
    link_paths = '/home/packerc/shared/metadata_db/data/link_to_zoon_id/'
    class_paths = '/home/packerc/shared/metadata_db/data/consensus_classifications/'
    seasons = [str(i) for i in range(1, 9)]
    # 35'000 empty in S11 training set
    sampling_size_per_season = 5000

    # read files
    res = dict()
    for s in seasons:
        zooid_to_img_mapper = dict()
        res[s] = {'zooid_to_img_mapper': zooid_to_img_mapper, 'blank_zooid': []}
        file_path_link = os.path.join(link_paths, 'S' + s + '_links.csv')
        file_path_blanks = os.path.join(class_paths, 'season_' + s + '_blanks.csv')
        file_comp = os.path.join(link_paths, 'S' + s + '_comparison.csv')
        file_db = os.path.join(link_paths, 'S' + s + '_db_captures.csv')
        # check if comparison file exists
        comp_exists = os.path.isfile(file_comp)
        if comp_exists:
            with open(file_comp, 'r') as f:
                csv_reader = csv.reader(f, delimiter=',')
                for line in csv_reader:
                    path = line[6]
                    zooid = line[8]
                    if zooid not in zooid_to_img_mapper:
                        zooid_to_img_mapper[zooid] = []
                    else:
                        zooid_to_img_mapper[zooid].append(path)

        # check if db captures file exists
        db_exists = os.path.isfile(file_db)
        if db_exists:
            # read links
            with open(file_path_link, 'r') as f:
                cid_to_zooid_mapper = dict()
                csv_reader = csv.reader(f, delimiter=',')
                for line in csv_reader:
                    zooid = line[1]
                    cid = line[0]
                    cid_to_zooid_mapper[cid] = zooid

            with open(file_db, 'r') as f:
                csv_reader = csv.reader(f, delimiter=',')
                for line in csv_reader:
                    path = line[6]
                    cid = line[0]
                    if cid in cid_to_zooid_mapper:
                        zooid = cid_to_zooid_mapper[cid]
                    else:
                        continue
                    # Map zooids to images
                    if zooid not in zooid_to_img_mapper:
                        zooid_to_img_mapper[zooid] = []
                    else:
                        zooid_to_img_mapper[zooid].append(path)

        with open(file_path_blanks, 'r') as f:
            csv_reader = csv.reader(f, delimiter=',')
            for line in csv_reader:
                zooid = line[0]
                res[s]['blank_zooid'].append(zooid)

    # Sample
    final_sample = list()
    for s, data in res.items():
        # sample blank events
        blank_events = set(data['blank_zooid'])
        blanks_with_images = set([x for x, ll in
            data['zooid_to_img_mapper'].items() if len(ll) > 0])
        # common
        blanks_to_sample = blank_events.intersection(blanks_with_images)

        blank_sample = random.sample(blanks_to_sample, sampling_size_per_season)
        # get image paths
        for blank in blank_sample:
            blank_images = data['zooid_to_img_mapper'][blank]
            if len(blank_images) == 0:
                continue
            # randomly sample one image
            blank_image = random.choice(blank_images)
            # correct image name
            blank_image = correct_image_name(blank_image)
            final_sample.append(blank_image)

    # Write to disk
    with open(output_file, 'w') as f:
        csv_writer = csv.writer(f, delimiter=',')
        for line in final_sample:
            csv_writer.writerow([line])
