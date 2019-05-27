""" Update ML scores for a subject set on Zooniverse based on a
    Manifest with ML scores """
import json
import os
from collections import OrderedDict
import argparse

from panoptes_client import Panoptes, Subject

from utils.utils import read_config_file, slice_generator


# project_id = '5155'
# subject_set_id = '38665'
# manifest_path = '/home/packerc/shared/zooniverse/Manifests/RUA/RUA_S1__batch_2__manifest_uploaded.json'
# tracker_file = '/home/packerc/will5448/data/misc/rua_update_tracker2.txt'

# args = dict()
# args['manifest_path'] = '/home/packerc/shared/zooniverse/Manifests/RUA/RUA_S1__batch_2__manifest_uploaded.json'
# args['tracker_file'] = '/home/packerc/will5448/data/misc/RUA_S1_update_ml_tracker.txt'
# args['verify_upload'] = True
# #
# SITE=RUA
# SEASON=RUA_S1
# python3 -m utils.update_ml_scores_on_zooniverse \
# --manifest_path /home/packerc/shared/zooniverse/Manifests/${SITE}/${SEASON}__batch_2__manifest_uploaded.json \
# --tracker_file /home/packerc/will5448/data/misc/${SEASON}_update_ml_tracker.txt
# --verify_upload


if __name__ == "__main__":

    # Parse command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest_path", type=str, required=True)
    parser.add_argument("--tracker_file", type=str, required=True)
    parser.add_argument("--verify_upload", action='store_true')

    args = vars(parser.parse_args())

    print("Reading Manifest", flush=True)
    with open(args['manifest_path'], 'r') as f:
        mani = json.load(f)
    print("Finished Reading Manifest", flush=True)

    if not os.path.isfile(args['tracker_file']):
        with open(args['tracker_file'], 'w') as f:
            f.writelines([''])
        print("Created Tracker File at {}".format(
            args['tracker_file']), flush=True)

    with open(args['tracker_file'], 'r') as f:
        tracker = f.read().splitlines()

    subjects_uploaded = OrderedDict((x, None) for x in tracker)
    print("Found {} records in tracker file".format(len(tracker)), flush=True)

    # create subject id to mapping
    subid_dict = dict()
    for k, v in mani.items():
        _id = v['info']['subject_id']
        meta_data = v["upload_metadata"]
        subid_dict[_id] = {k: v for k, v in meta_data.items() if k.startswith('#machine')}

    # subjects to update
    subjects_to_update = list(subid_dict.keys() - subjects_uploaded.keys())
    print("{} subjects remain for update".format(
        len(subjects_to_update)), flush=True)

    config = read_config_file('~/keys/passwords.ini')
    Panoptes.connect(username=config['zooniverse']['username'],
                     password=config['zooniverse']['password'])
    n_updated = 0
    print("Starting to update subjects", flush=True)

    n_to_update = len(subjects_to_update)
    slices = slice_generator(n_to_update, n_to_update // 100)

    for i_start, i_end in slices:
        subjects_updated = list()
        subject_objects = list()
        with Subject.async_saves():
            for subject_id in subjects_to_update[i_start:i_end]:
                subject = Subject.find(subject_id)
                new_data = subid_dict[subject_id]
                if new_data.items() <= subject.metadata.items():
                    print("Already updated subject {}".format(
                        subject_id), flush=True)
                    subjects_updated.append(subject_id)
                    n_updated += 1
                    continue
                subject.metadata.update(new_data)
                subject.save()
                subject_objects.append(subject)
        # verify save status
        for subject in subject_objects:
            if subject.async_save_result:
                subjects_updated.append(subject.id)
                n_updated += 1
            else:
                print("Failed to save subject {}".format(
                    subject.id), flush=True)
        print("updated {} subjects".format(n_updated), flush=True)
        with open(args['tracker_file'], 'a') as f:
            for line in subjects_updated:
                f.write(line + '\n')
        print("Updated tracker file at {}".format(
            args['tracker_file']), flush=True)
    print("Finished updating subjects", flush=True)




    # for i_start, i_end in slices:
    #     subjects_updated = list()
    #     for subject_id in subjects_to_update[i_start:i_end]:
    #         subject = Subject.find(subject_id)
    #         new_data = subid_dict[subject_id]
    #         if new_data.items() <= subject.metadata.items():
    #             print("Already updated subject {}".format(subject_id), flush=True)
    #             subjects_updated.append(subject_id)
    #             n_updated += 1
    #             continue
    #         subject.metadata.update(new_data)
    #         subject.save()
    #         if args['verify_upload']:
    #             subject_updated = Subject.find(subject_id)
    #             if new_data.items() <= subject_updated.metadata.items():
    #                 subjects_updated.append(subject_id)
    #                 n_updated += 1
    #             else:
    #                 print("Failed to save subject {}".format(
    #                     subject_id), flush=True)
    #         else:
    #             subjects_updated.append(subject_id)
    #             n_updated += 1
    #     print("updated {} subjects".format(n_updated), flush=True)
    #     with open(args['tracker_file'], 'a') as f:
    #         for line in subjects_updated:
    #             f.write(line + '\n')
    #     print("Updated tracker file at {}".format(
    #         args['tracker_file']), flush=True)
    # print("Finished updating subjects", flush=True)




    # for i_start, i_end in slices:
    #     subjects_updated = list()
    #     with Subject.async_saves():
    #         for subject_id in subjects_to_update[i_start:i_end]:
    #             subject = Subject.find(subject_id)
    #             new_data = subid_dict[subject_id]
    #             subject.metadata.update(new_data)
    #             subject.save()
    #             subjects_updated.append(subject_id)
    #             n_updated += 1
    #             else:
    #                 print("Failed to save subject {}".format(
    #                     subject_id), flush=True)
    #     print("updated {} subjects".format(n_updated), flush=True)
    #     with open(args['tracker_file'], 'a') as f:
    #         for line in subjects_updated:
    #             f.write(line + '\n')
    #     print("Updated tracker file at {}".format(
    #         args['tracker_file']), flush=True)
    # print("Finished updating subjects", flush=True)
