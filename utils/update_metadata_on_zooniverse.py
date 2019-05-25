""" Update MetaData of a subject on Zooniverse based on a pre-defined logic to
    fix legacy data - dont use this if you dont know what it does
"""
import os
import pandas as pd
from collections import OrderedDict
import argparse

from panoptes_client import Panoptes, Subject

from utils.utils import read_config_file, slice_generator
from zooniverse_uploads import uploader


# project_id = '5155'
# subject_set_id = '38665'
# manifest_path = '/home/packerc/shared/zooniverse/Manifests/RUA/RUA_S1__batch_2__manifest_uploaded.json'

# args = dict()
# args['subjects_to_update_csv'] = '/home/packerc/shared/zooniverse/Exports/NIA/NIA_S1_subjects.csv'
# args['tracker_file'] = '/home/packerc/will5448/data/misc/nia_metadata_update_tracker.txt'
# args['season_id_to_add'] = 'NIA_S1'
# args['dry_run'] = True


# SITE=NIA
# SEASON=NIA_S1
# python3 -m utils.update_metadata_on_zooniverse \
# --subjects_to_update_csv /home/packerc/shared/zooniverse/Exports/${SITE}/${SEASON}_subjects.csv \
# --season_id_to_add ${SEASON} \
# --tracker_file /home/packerc/will5448/data/misc/${SEASON}_metadata_update_tracker.txt \
# --dry_run


if __name__ == "__main__":

    # Parse command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("--subjects_to_update_csv", type=str, required=True)
    parser.add_argument("--season_id_to_add", type=str, default='')
    parser.add_argument("--tracker_file", type=str, required=True)
    parser.add_argument("--dry_run", action='store_true')

    args = vars(parser.parse_args())

    print("Reading Subjects File", flush=True)
    df = pd.read_csv(args['subjects_to_update_csv'], dtype=str)

    print("Read {} records".format(df.shape[0]), flush=True)

    subject_ids = list(df['subject_id'])

    if not os.path.isfile(args['tracker_file']):
        with open(args['tracker_file'], 'w') as f:
            f.writelines([''])
        print("Created Tracker File at {}".format(
            args['tracker_file']), flush=True)

    with open(args['tracker_file'], 'r') as f:
        tracker = f.read().splitlines()

    subjects_already_updated = OrderedDict((x, None) for x in tracker)
    print("Found {} records in tracker file".format(len(tracker)), flush=True)

    # subjects to update
    subjects_to_update = list(set(subject_ids) - subjects_already_updated.keys())
    print("{} subjects remain for update".format(
        len(subjects_to_update)), flush=True)

    config = read_config_file('~/keys/passwords.ini')
    Panoptes.connect(username=config['zooniverse']['username'],
                     password=config['zooniverse']['password'])
    # my_project = Project(args['project_id'])
    # my_set = SubjectSet().find(args['subject_set_id'])

    n_updated = 0
    print("Starting to update subjects", flush=True)
    subjects_updated = list()

    n_to_update = len(subjects_to_update)
    slices = slice_generator(n_to_update, n_to_update // 100)

    for i_start, i_end in slices:
        with Subject.async_saves():
            for subject_id in subjects_to_update[i_start:i_end]:
                subject = Subject.find(subject_id)
                meta_to_update = dict()
                # update season field
                if not '#season' in subject.metadata:
                    if args['season_id_to_add'] != '':
                        meta_to_update['#season'] = args['season_id_to_add']
                # add capture_id
                if not '#capture_id' in subject.metadata:
                    if '#season' in meta_to_update:
                        season = meta_to_update['#season']
                    else:
                        season = subject.metadata['#season']
                    site = subject.metadata['#site']
                    roll = subject.metadata['#roll']
                    capture = subject.metadata['#capture']
                    capture_id = '{season}#{site}#{roll}#{capture}'.format(
                        **{'season': season,
                         'site': site,
                         'roll': roll,
                         'capture': capture})
                    meta_to_update['#capture_id'] = capture_id
                # add capture_id_anonymized
                if not 'capture_id_anonymized' in subject.metadata:
                    if '#capture_id' in subject.metadata:
                        anonym = uploader.anonymize_id(subject.metadata['#capture_id'])
                        meta_to_update['capture_id_anonymized'] = anonym
                    elif '#capture_id' in meta_to_update:
                        anonym = uploader.anonymize_id(meta_to_update['#capture_id'])
                        meta_to_update['capture_id_anonymized'] = anonym
                    else:
                        pass
                # remove capture id
                if 'capture_id' in subject.metadata:
                    subject.metadata.pop('capture_id', None)
                # print
                if n_updated <= 10:
                    print("Updating From:", flush=True)
                    print(subject.metadata, flush=True)
                    print("=====================================", flush=True)
                subject.metadata.update(meta_to_update)
                if n_updated <= 10:
                    print("Updating To:", flush=True)
                    print(subject.metadata, flush=True)
                    print("=====================================", flush=True)
                if not args['dry_run']:
                    if len(meta_to_update.keys()) > 0:
                        subject.save()
                subjects_updated.append(subject_id)
                n_updated += 1
        print("updated {} subjects".format(n_updated), flush=True)
        with open(args['tracker_file'], 'a') as f:
            for line in subjects_updated:
                f.write(line + '\n')
        print("Updated tracker file at {}".format(
            args['tracker_file']), flush=True)
        subjects_updated = list()

    print("Finished updating subjects", flush=True)
