""" Zooniverse Uploader """
import os
import hashlib
import csv

from panoptes_client import SubjectSet, Subject


def create_subject(project, media_files, metadata):
    """ Create a subject
        Args:
        - project: a Project() object defining the Zooniverse project
        - media_files: a list of media files to link to the subject
        - metadata: a dictionary with metadata to attach
    """
    subject = Subject()
    subject.links.project = project
    for media in media_files:
        subject.add_location(media)
    subject.metadata.update(metadata)
    subject.save()
    return subject


def create_subject2(project, media_files, metadata):
    """ Create a subject
        Args:
        - project: a Project() object defining the Zooniverse project
        - media_files: a list of media files to link to the subject
        - metadata: a dictionary with metadata to attach
    """
    subject = Subject()
    subject.links.project = project
    for media in media_files:
        subject.add_location(media)
    subject.metadata.update(metadata)
    try:
        subject.save()
    except TypeError:
        print("Type error catched -- ignoring")
    except Exception:
        raise
    return subject


def handle_batch_failure(subjects_to_link):
    print('Rolling back, attempting to clean up any unlinked subjects.')
    for subject in subjects_to_link:
        print('Removing the subject with id: {}'.format(subject.id))
        subject.delete()


def create_tracker_file(file_path):
    with open(file_path, 'w') as f:
        f.write('unique_id,subject_id\n')


def update_tracker_file(file_path, unique_ids, subject_ids):
    if not os.path.exists(file_path):
        create_tracker_file(file_path)
    with open(file_path, 'a') as f:
        n_records = len(unique_ids)
        for i in range(0, n_records):
            line_to_write = ','.join([unique_ids[i], subject_ids[i]])
            f.write('%s\n' % line_to_write)


def read_tracker_file(file_path):
    tracker_data = dict()

    with open(file_path, newline='', mode='r') as csvfile:
        csv_reader = csv.reader(csvfile, delimiter=',')
        _ = next(csv_reader)
        for row in csv_reader:
            unique_id = row[0]
            subject_id = row[1]
            tracker_data[unique_id] = subject_id

    return tracker_data


def create_subject_set(project, subject_set_name):
    # Create a new subject set
    new_set = SubjectSet()
    new_set.links.project = project
    new_set.display_name = subject_set_name
    new_set.save()
    project.add_subject_sets(new_set)
    return new_set


def anonymize_id(_id):
    return hashlib.sha1(str.encode(_id)).hexdigest()


def add_batch_to_subject_set(subject_set, subjects):
    print('Linking {} subjects to the set with id: {}'.format(
        len(subjects), subject_set.id), flush=True)
    subject_set.add(subjects)
