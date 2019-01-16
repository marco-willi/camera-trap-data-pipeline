""" Create a Tracker File of an Existing Subject-Set """

from panoptes_client import Project, Panoptes, SubjectSet
from zooniverse_uploads import uploader
from utils import (
    read_config_file)

args = {'project_id': '5880',
        'subject_set_id': '71880'}
tracker_file = '/home/packerc/shared/zooniverse/Manifests/KAR/upload_tracker_file.txt'

# project id
config = read_config_file('~/keys/passwords.ini')

# connect to panoptes
Panoptes.connect(username=config['zooniverse']['username'],
                 password=config['zooniverse']['password'])

# Get Project
my_project = Project(args['project_id'])
my_set = SubjectSet().find(args['subject_set_id'])

print("Subject set found, looking for already uploaded subjects",
      flush=True)

# find already uploaded subjects
n_already_uploaded = 0
for i, subject in enumerate(my_set.subjects):
    n_already_uploaded += 1
    if (i % 100) == 0:
        print("Found %s uploaded records and counting..." % i,
              flush=True)
    roll = subject.metadata['#roll']
    site = subject.metadata['#site']
    capture = subject.metadata['#capture']
    season = subject.metadata['#season']
    capture_id = '#'.join([season, site, roll, capture])
    uploader.update_tracker_file(tracker_file, [capture_id], [subject.id])
