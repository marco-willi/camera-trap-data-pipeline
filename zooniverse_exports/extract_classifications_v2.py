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
import csv
from collections import Counter
import traceback

from zooniverse_exports import extractor


# Cedar Creek
args = dict()
args['classification_csv'] = '/home/packerc/shared/zooniverse/Exports/CC/CC_S1_classifications.csv'
args['output_csv'] = '/home/packerc/shared/zooniverse/Exports/CC/CC_S1_classifications_extracted_v2.csv'
args['workflow_id'] = None
args['workflow_version'] = None


args = dict()
args['classification_csv'] = '/home/packerc/shared/zooniverse/Exports/RUA/RUA_S1_classifications.csv'
args['output_csv'] = '/home/packerc/shared/zooniverse/Exports/RUA/RUA_S1_classifications_extracted_v2.csv'
args['workflow_id'] = None
args['workflow_version'] = None

args = dict()
args['classification_csv'] = '/home/packerc/shared/zooniverse/Exports/GRU/GRU_S1_classifications.csv'
args['output_csv'] = '/home/packerc/shared/zooniverse/Exports/GRU/GRU_S1_classifications_extracted_v2.csv'
args['workflow_id'] = None
args['workflow_version'] = None



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
        eligible = extractor.is_eligible(
            line, row_name_to_id_mapper, classification_condition)
        if not eligible:
            continue
        try:
            # extract classification-level info
            classification_info = extractor.extract_classification_info(
                line, row_name_to_id_mapper, flags)
            # map classification info header
            classification_info = extractor.rename_dict_keys(
                classification_info, flags['CLASSIFICATION_INFO_MAPPER'])
            # get all annotations (list of annotations)
            annotations_list = extractor.extract_annotations_from_json(
                line, row_name_to_id_mapper)
            # if classification_info['classification_id'] == '142058886':
            #     break
            # get all tasks of an annotation
            for task in annotations_list:
                if not extractor.task_is_completed(task):
                    n_incomplete_tasks += 1
                    continue
                task_type = extractor.identify_task_type(task)
                ids_or_answers = extractor.extract_task_info(
                    task, task_type, flags)
                # get all identifications/answers of a task
                for _id_answer in ids_or_answers:
                    _id_answer_mapped = extractor.map_task_questions(
                        _id_answer, flags)
                    record = {**classification_info,
                              'annos': _id_answer_mapped}
                    all_records.append(record)
        except Exception:
            print("Error - Skipping Record %s" % line_no)
            print("Full line:\n %s" % line)
            print(traceback.format_exc())

print("Processed {} classifications".format(line_no))
print("Extracted {} tasks".format(len(all_records)))
print("Incomplete tasks: {}".format(n_incomplete_tasks))

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


######################################
# Unpack Classifications into
# Annotations
######################################

# get all possible answers to the questions
question_answers = extractor.define_question_answers(all_records)

# analyze the question types
question_types = extractor.analyze_question_types(all_records)

# build question header for csv export
question_header = extractor.build_question_header(
    question_answers, question_types)

# modify question column names
question_header_print = list()
for question in question_header:
    question_header_print.append(
        flags['QUESTION_DELIMITER'].join([flags['QUESTION_PREFIX'], question]))

######################################
# Export
######################################

# build csv header
classification_header_cols = flags['CLASSIFICATION_INFO_TO_ADD']
classification_header_cols = [
    flags['CLASSIFICATION_INFO_MAPPER'][x] if x
    in flags['CLASSIFICATION_INFO_MAPPER'] else x for
    x in classification_header_cols]
header = classification_header_cols + question_header_print

with open(args['output_csv'], 'w') as f:
    csv_writer = csv.writer(f, delimiter=',')
    print("Writing output to %s" % args['output_csv'])
    csv_writer.writerow(header)
    tot = len(all_records)
    for line_no, record in enumerate(all_records):
        # get classification info data
        class_data = [record[x] for x in classification_header_cols]
        # get annotation info data
        answers = extractor.flatten_annotations(
            record['annos'], question_types,  question_answers)
        answers_ordered = [
            answers[x] if x in answers else '' for x
            in question_header]
        csv_writer.writerow(class_data + answers_ordered)
