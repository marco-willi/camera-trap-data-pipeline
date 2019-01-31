""" Extract Zooniverse Classifications

    Arguments:
    --------------
    - classification_csv (str):
        Path to classification file as downloaded from Zooniverse
    - output_csv (str):
        Path to new extracted csv file (will be overwritten)
    - workflow_id (int):
        Workflow id of the classifications to extract
    - workflow version (int):
        Worfklow version of the classifications to extract

    Example Usage:
    --------------
    python3 extract_classifications.py \
            -classification_csv classifications.csv \
            -output_csv classifications_extracted.csv \
            -workflow_id 4655 \
            -workflow_version 304
"""
import json
import csv
import copy
import argparse
import time
from collections import OrderedDict
from collections import Counter
import traceback

from utils import print_progress
from zooniverse_exports import extractor


# Cedar Creek
args = dict()
args['classification_csv'] = '/home/packerc/shared/zooniverse/Exports/CC/CC_S1_classifications.csv'
args['output_csv'] = '/home/packerc/shared/zooniverse/Exports/CC/CC_S1_classifications_extracted_v2.csv'
args['worfklow_ids'] = None
args['worfklow_versions'] = None

args = dict()
args['classification_csv'] = '/home/packerc/shared/zooniverse/Exports/RUA/RUA_S1_classifications.csv'
args['output_csv'] = '/home/packerc/shared/zooniverse/Exports/RUA/RUA_S1_classifications_extracted_v2.csv'
args['worfklow_ids'] = None
args['worfklow_versions'] = None

args = dict()
args['classification_csv'] = '/home/packerc/shared/zooniverse/Exports/GRU/GRU_S1_classifications.csv'
args['output_csv'] = '/home/packerc/shared/zooniverse/Exports/GRU/GRU_S1_classifications_extracted_v2.csv'
args['worfklow_ids'] = None
args['worfklow_versions'] = None


######################################
# Configuration
######################################

# One classification contains 1:N annotations
# One annotation contains 1:N task(to be verified!)
# One task contains 1:N identifications (for survey task)
# One task contains 1:N answers (for questions task)
# One identification contains 1:N answers (for survey task)

flags = dict()

flags['QUESTION_PREFIX'] = 'question'
flags['QUESTION_DELIMITER'] = '__'

flags['QUESTION_NAME_MAPPER'] = {
    'howmany': 'count',
    'question': 'species',
    'arethereanyyoungpresent': 'young_present',
    'doyouseeanyhorns': 'horns_visible',
    'choice': 'species',
    'doyouseeanyantlers': 'antlers_visible'
    }

flags['ANSWER_DEFAULTS_FOR_EXPORT'] = {
    'count': '',
    'species': '',
    'young_present': '',
    'horns_visible': ''
    }

flags['ANSWER_TYPE_MAPPER'] = {
    'species': {
        'no animals present': 'blank',
        'nothing': 'blank',
        'nothinghere': 'blank'
        }
    }

flags['QUESTIONS_TO_IGNORE'] = ('dontcare')

flags['CLASSIFICATION_INFO_TO_ADD'] = [
    'user_name', 'user_id', 'created_at', 'subject_ids',
    'workflow_id', 'workflow_version', 'classification_id']

flags['CLASSIFICATION_INFO_MAPPER'] = {
    'subject_ids': 'subject_id'
}


classification_condition = dict()
if args['workflow_id'] is not None:
    classification_condition['workflow_id'] = args['workflow_id']
if args['workflow_version'] is not None:
    classification_condition['workflow_version'] = args['workflow_version']


######################################
# Read and Process Classifications
######################################

all_records = list()
n_incomplete_tasks = 0
with open(args['classification_csv'], "r") as ins:
    csv_reader = csv.reader(ins, delimiter=',', quotechar='"')
    header = next(csv_reader)
    row_name_to_id_mapper = {x: i for i, x in enumerate(header)}
    row_id_to_name_mapper = {i: x for i, x in enumerate(header)}
    for line_no, line in enumerate(csv_reader):
        # print status
        if ((line_no % 10000) == 0) and (line_no > 0):
            print("Processed %s classifications" % line_no)
        # check eligibility of classification
        if not is_eligible(line, row_name_to_id_mapper):
            continue
        try:
            # extract classification-level info
            classification_info = extractor.extract_classification_info(
                line, row_name_to_id_mapper, flags)
            # map classification info header
            classification_info = extractor.ename_dict_keys(
                classification_info, flags['CLASSIFICATION_INFO_MAPPER'])
            # get all annotations (list of annotations)
            annotations_list = extractor.extract_annotations_from_json(
                line, row_name_to_id_mapper)
            # if classification_info['classification_id'] == '142058886':
            #     break
            # get all tasks of an annotation
            for task in annotations_list:
                if not extractor.task_is_completed(task):
                    if n_incomplete_tasks < 10:
                        print("Incomplete task - skipping... %s" % task)
                    if n_incomplete_tasks == 10:
                        print("Stop printing incomplete tasks...")
                    n_incomplete_tasks += 1
                    continue
                task_type = extractor.identify_task_type(task)
                ids_or_answers = extractor.extract_task_info(
                    task, task_type, flags)
                # get all identifications/answers of a task
                for _id_answer in ids_or_answers:
                    _id_answer_mapped = extractor.map_task_questions(
                        _id_answer)
                    record = {**classification_info,
                              'annos': _id_answer_mapped}
                    all_records.append(record)
        except Exception:
            print("Error - Skipping Record %s" % line_no)
            print("Full line:\n %s" % line)
            print(traceback.format_exc())

######################################
# Analyse Classifications
######################################

# Analyse the dataset
question_stats = dict()
user_stats = dict()
not_logged_in_counter = 0
worfklow_stats = dict()

for record in all_records:
    # get annotation information
    for anno in record['annos']:
        # get question/answer stats
        for question, answers in anno.items():
            if question not in question_stats:
                question_stats[question] = Counter()
            if not isinstance(answers, list):
                question_stats[question].update([answers])
            else:
                question_stats[question].update(answers)
    # get workflow information
    if ('workflow_id' in record) and ('workflow_version' in record):
        wid = record['workflow_id']
        wv = record['workflow_version']
        if wid not in worfklow_stats:
            worfklow_stats[wid] = Counter()
        worfklow_stats[wid].update([wv])
    # get user information
    if ('user_name' in record) and ('user_id' in record):
        uid = record['user_id']
        un = record['user_name']
        if uid == '' and un.startswith('not-logged-in-'):
            not_logged_in_counter += 1
        else:
            if un not in user_stats:
                user_stats[un] = {'classifications': set()}
            user_stats[un]['classifications'].add(record['classification_id'])

# print header info
print("Found the following questions/tasks: {}".format(
    [x for x in question_stats.keys()]))

# Stats not-logged-in users
print("Number of classifications by not logged in users: {}".format(
    not_logged_in_counter))

# print label stats
for question, answer_data in question_stats.items():
    print("Stats for question: %s" % question)
    total = sum([x for x in answer_data.values()])
    for answer, count in answer_data.most_common():
        print("Answer: {:20} -- counts: {:10} / {} ({:.2f} %)".format(
            answer, count, total, 100*count/total))
# workflow stats
print("Workflow stats:")
for workflow_id, workflow_version_data in worfklow_stats.items():
    for workflow_version, count in workflow_version_data.items():
        print("Workflow id: {:7} Workflow version: {:10} -- counts: {}".format(
              workflow_id, workflow_version, count))
# user stats
user_n_classifications = Counter()
for user_name, user_data in user_stats.items():
    n_class = len(user_data['classifications'])
    user_n_classifications.update({user_name: n_class})
print("The top-10 most active users are:")
for i, (user, count) in enumerate(user_n_classifications.most_common(10)):
    print("Rank {:3} - User: {:20} - Classifications: {}".format(
        i+1, user, count))


# # inspect special case
# user_name = 'sap46'
# subject_id = '25219686'
#
# for record in all_records:
#     uid = record['user_id']
#     un = record['user_name']
#     sid = record['subject_ids']
#     if (un == user_name) and (sid == subject_id):
#         print(record)


######################################
# Unpack Classifications into
# Annotations
######################################


# Export Each Identification
questions = list(question_stats)
header = CLASSIFICATION_INFO_TO_ADD + questions

def unpack_annotations(annotations):
    res = dict()
    for question_answer in annotations:
        for question, answers in question_answer.items():
            if isinstance(answers, list):
                for answer in answers:
                    res[answer] = '1'
            else:
                res[question] = answers
    return res

with open(args['output_csv'], 'w') as f:
    csv_writer = csv.writer(f, delimiter=',')
    print("Writing output to %s" % args['output_csv'])
    csv_writer.writerow(header)
    tot = len(all_records)
    for line_no, record in enumerate(all_records):
        # get classification info data
        class_data = [record[x] for x in CLASSIFICATION_INFO_TO_ADD]
        # get annotation info data
        answers = unpack_annotations(record['annos'])
        answers_ordered = [answers[x] if x in answers else '' for x in questions]
        csv_writer.writerow(class_data + answers_ordered)
        print_progress(line_no, tot)


# compile the current record
all_extractions[line_no] = {**class_info, 'annos': extracted_annotations}
if len(extracted_annotations) > 1:
    print(all_extractions[line_no])
for ex in extracted_annotations:
    if isinstance(ex, list):
        if len(ex) > 1:
            print(all_extractions[line_no])


# get workflow versions and id
workflow_counter = dict()
workflow_id = class_info['workflow_id']
workflow_version = class_info['workflow_version']
if workflow_id not in workflow_counter:
    workflow_counter[workflow_id] = dict()
    if workflow_version not in workflow_counter[workflow_id]:
        workflow_counter[workflow_id][workflow_version] = 0
    workflow_counter[workflow_id][workflow_version] += 1



############################
# Parameters Fixed
############################

# Define the fields of a Snapshot Safari Record
record_names = ['species', 'count', 'moving',
                'eating', 'standing', 'resting', 'interacting',
                'young_present']

# Define the default values of a Snapshot Safari Record
record_defaults = ['default', '0', '0', '0', '0', '0', '0', '0']

snapshot_safari_default_record = OrderedDict(
        (i, j) for i, j in zip(record_names, record_defaults))

# Define the fields of a Snapshot Safari Annotation
annotation_record = ['subject_id', 'user_name', 'created_at'] + \
                    record_names

    ############################
    # Helper Functions
    ############################

    def post_process_anno(anno, record_fields=annotation_record):
        """ Post Processing of Annotations """

        species_field = record_fields.index('species')

        # Set nothing here fields to default
        if anno[species_field] == 'NOTHINGHERE':
            pass

        # Map Species Field
        map_choices = {'No animals present': 'NOTHINGHERE'}

        if anno[species_field] in map_choices:
            anno[species_field] = map_choices[anno[species_field]]

        return anno

    def extract_meta_data(line, mapper):
        """ Extract Meta data """
        meta_data = line[mapper['metadata']]
        meta_dict = json.loads(meta_data)
        return meta_dict

    def extract_annos(line, mapper):
        """ Extract Annotations """
        data = line[mapper['annotations']]
        dic = json.loads(data)
        return dic

    def extract_tasks(annos):
        """ Extract Tasks """
        extracted = dict()
        for task in annos:
            extracted[task['task']] = task
        return extracted

    def task_is_completed(task):
        """ Check if task has been completed """
        return len(task['value']) > 0

    def extract_question_task(task_value, default=snapshot_safari_default_record):
        """ Extract T1 task (shortcut task) """
        value = task_value['value'][0]
        default['species'] = value
        return default

    def extract_survey_task(task_value, default=snapshot_safari_default_record):
        """ Extract T0 task (survey task) """
        value = task_value['value']
        answers = list()
        for answer in value:
            default_c = copy.copy(default)
            default_c['species'] = answer['choice']
            if 'HOWMANY' in answer['answers']:
                default_c['count'] = answer['answers']['HOWMANY']

            if 'MOVING' in answer['answers']['WHATBEHAVIORSDOYOUSEE']:
                default_c['moving'] = '1'

            if 'EATING' in answer['answers']['WHATBEHAVIORSDOYOUSEE']:
                default_c['eating'] = '1'

            if 'STANDING' in answer['answers']['WHATBEHAVIORSDOYOUSEE']:
                default_c['standing'] = '1'

            if 'RESTING' in answer['answers']['WHATBEHAVIORSDOYOUSEE']:
                default_c['resting'] = '1'

            if 'INTERACTING' in answer['answers']['WHATBEHAVIORSDOYOUSEE']:
                default_c['interacting'] = '1'

            if 'ARETHEREANYYOUNGPRESENT' in answer['answers']:
                if answer['answers']['ARETHEREANYYOUNGPRESENT'] == 'YES':
                    default_c['young_present'] = '1'

            answers.append(default_c)

        return answers

    def extract_task_values(tasks):
        """ Extract 1-N tasks from annotations """

        # Loop over tasks
        extractions = list()
        for task_name, task_value in tasks.items():
            if task_name == 'T1':
                if task_is_completed(task_value):
                    extracted = extract_t1_task(task_value)
                    extractions.append(extracted)
            elif task_name == 'T0':
                if task_is_completed(task_value):
                    extracted = extract_t0_task(task_value)
                    extractions.append(extracted)
            elif task_name == 'T4':
                if task_is_completed(task_value):
                    extracted = extract_t1_task(task_value)
                    extractions.append(extracted)

        return extractions

    def check_eligibility(line, w_id, w_v, mapper):
        """ Check whether classification is eligible """
        w_v_major = line[mapper['workflow_version']].split('.')[0]
        return all([line[mapper['workflow_id']] == w_id,
                    w_v_major == w_v])

    def find_n_tasks(task_values):
        """ Determine the number of tasks made in a classification """
        if len(task_values) > 0:
            if isinstance(task_values[0], list):
                return len(task_values[0])
            else:
                return len(task_values)
        else:
            return 0

    def get_task_x(task_values, x):
        """ Get Task X from list of Tasks """
        if isinstance(task_values[0], list):
            return task_values[0][x]
        elif isinstance(task_values[x], list):
            return task_values[x][0]
        else:
            return task_values[x]

    annos_extracted = list()

    with open(input_file, "r") as ins:
        csv_reader = csv.reader(ins, delimiter=',', quotechar='"')
        for _id, line in enumerate(csv_reader):
            if (_id % 10000) == 0:
                print("Processing Classification %s" % _id)
            # extract header
            if _id == 0:
                row_name_to_id_mapper = {x: i for i, x in enumerate(line)}
                row_id_to_name_mapper = {i: x for i, x in enumerate(line)}
            else:
                if not check_eligibility(line, workflow_id,
                                         workflow_version_major,
                                         row_name_to_id_mapper):
                    continue

                try:
                    # Extract data
                    meta_dict = extract_meta_data(line, row_name_to_id_mapper)
                    annos = extract_annos(line, row_name_to_id_mapper)
                    tasks = extract_tasks(annos)
                    task_values = extract_task_values(tasks)

                    # Build annotation records
                    n_tasks = find_n_tasks(task_values)

                    for j in range(0, n_tasks):
                        user_id = line[row_name_to_id_mapper['user_name']]
                        created_at = line[row_name_to_id_mapper['created_at']]
                        subject_id = line[row_name_to_id_mapper['subject_ids']]
                        task_annos = get_task_x(task_values, j)

                        anno_record = [subject_id, user_id, created_at] + \
                                      [task_annos[x] for x in
                                       snapshot_safari_default_record.keys()]
                        anno_record = post_process_anno(anno_record)
                        annos_extracted.append(anno_record)

                except Exception:
                    print("Error - Skipping Record %s" % _id)
                    print("Full line:\n %s" % line)
                    print(traceback.format_exc())
                    continue

    # Calc statistics
    stats = {k: [] for k in record_names}
    for anno in annos_extracted:
        for name in record_names:
            i = annotation_record.index(name)
            stats[name].append(anno[i])

    # print stats
    for stat_name, stat_list in stats.items():
        print("STAT: %s" % stat_name)
        print(Counter(stat_list))

    with open(output_file, "w", newline='') as outs:
        csv_writer = csv.writer(outs, delimiter=',')
        print("Writing file to %s" % output_file)
        csv_writer.writerow(annotation_record)
        tot = len(annos_extracted)
        for i, line in enumerate(annos_extracted):
            print_progress(i, tot)
            csv_writer.writerow(line)
