""" Extract Zooniverse Classifications
    - Extract annotations from classifications
    - Export to csv file
"""
import csv
from collections import Counter
import traceback
import os
import argparse
import logging
from logger import setup_logger, create_logfile_name

from zooniverse_exports import extractor
from utils import print_nested_dict


# # Cedar Creek
# args = dict()
# args['classification_csv'] = '/home/packerc/shared/zooniverse/Exports/CC/CC_S1_classifications.csv'
# args['output_csv'] = '/home/packerc/shared/zooniverse/Exports/CC/CC_S1_classifications_extracted_v2.csv'
# args['workflow_id'] = None
# args['workflow_version'] = None
#
#
# args = dict()
# args['classification_csv'] = '/home/packerc/shared/zooniverse/Exports/RUA/RUA_S1_classifications.csv'
# args['output_csv'] = '/home/packerc/shared/zooniverse/Exports/RUA/RUA_S1_classifications_extracted_v2.csv'
# args['workflow_id'] = None
# args['workflow_version'] = None
#
# args = dict()
# args['classification_csv'] = '/home/packerc/shared/zooniverse/Exports/GRU/GRU_S1_classifications.csv'
# args['output_csv'] = '/home/packerc/shared/zooniverse/Exports/GRU/GRU_S1_classifications_extracted_v2.csv'
# args['workflow_id'] = None
# args['workflow_version'] = None


if __name__ == '__main__':

    # Parse command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("--classification_csv", type=str, required=True)
    parser.add_argument("--output_csv", type=str, required=True)
    parser.add_argument("--workflow_id", type=str, default=None)
    parser.add_argument("--workflow_version", type=str, default=None)

    args = vars(parser.parse_args())

    ######################################
    # Configuration
    ######################################

    # logging
    log_file_name = create_logfile_name('extract_classifications')
    log_file_path = os.path.join(
        os.path.dir(args['output_csv']), log_file_name)
    setup_logger(log_file_path)
    logger = logging.getLogger(__name__)

    for k, v in args.items():
        logger.info("Argument {}: {}".format(k, v))

    # Flag variables that define the behavior of the extraction
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
            'nothinghere': 'blank',
            'nothingthere': 'blank'
            }
        }

    flags['QUESTIONS_TO_IGNORE'] = ('dontcare')

    flags['CLASSIFICATION_INFO_TO_ADD'] = [
        'user_name', 'user_id', 'created_at', 'subject_ids',
        'workflow_id', 'workflow_version', 'classification_id']

    flags['CLASSIFICATION_INFO_MAPPER'] = {
        'subject_ids': 'subject_id'
    }

    flags['SUBJECT_INFO_TO_ADD'] = ['#season', '#site', '#roll', '#capture']
    flags['SUBJECT_INFO_MAPPER'] = {
        '#season': 'season', '#site': 'site',
        '#roll': 'roll', '#capture': 'capture'}

    # logging flags
    print_nested_dict('', flags)

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
                print("Processed {:,} classifications".format(line_no))
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
                # extract subject-level data
                subject_info_raw = extractor.extract_key_from_json(
                    line, 'subject_data', row_name_to_id_mapper
                    )[classification_info['subject_id']]
                subject_info_to_add = dict()
                for field in flags['SUBJECT_INFO_TO_ADD']:
                    try:
                        subject_info_to_add[field] = subject_info_raw[field]
                    except:
                        subject_info_to_add[field] = ''
                subject_info_to_add = extractor.rename_dict_keys(
                    subject_info_to_add, flags['SUBJECT_INFO_MAPPER'])
                # get all annotations (list of annotations)
                annotations_list = extractor.extract_key_from_json(
                    line, 'annotations', row_name_to_id_mapper)
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
                        record = {**classification_info, **subject_info_to_add,
                                  'annos': _id_answer_mapped}
                        all_records.append(record)
            except Exception:
                logger.warning("Error - Skipping Record %s" % line_no)
                logger.warning("Full line:\n %s" % line)
                logger.warning(traceback.format_exc())

    logger.info("Processed {:,} classifications".format(line_no))
    logger.info("Extracted {:,} tasks".format(len(all_records)))
    logger.info("Incomplete tasks: {:,}".format(n_incomplete_tasks))

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
                user_stats[un]['classifications'].add(
                    record['classification_id'])

    # print header info
    logger.info("Found the following questions/tasks: {}".format(
        [x for x in question_stats.keys()]))

    # Stats not-logged-in users
    logger.info("Number of classifications by not logged in users: {}".format(
        not_logged_in_counter))

    # print label stats
    for question, answer_data in question_stats.items():
        logger.info("Stats for question: %s" % question)
        total = sum([x for x in answer_data.values()])
        for answer, count in answer_data.most_common():
            logger.info("Answer: {:20} -- counts: {:10} / {} ({:.2f} %)".format(
                answer, count, total, 100*count/total))
    # workflow stats
    logger.info("Workflow stats:")
    for workflow_id, workflow_version_data in worfklow_stats.items():
        for workflow_version, count in workflow_version_data.items():
            logger.info("Workflow id: {:7} Workflow version: {:10} -- counts: {}".format(
                  workflow_id, workflow_version, count))
    # user stats
    user_n_classifications = Counter()
    for user_name, user_data in user_stats.items():
        n_class = len(user_data['classifications'])
        user_n_classifications.update({user_name: n_class})

    logger.info("The top-10 most active users are:")
    for i, (user, count) in enumerate(user_n_classifications.most_common(10)):
        logger.info("Rank {:3} - User: {:20} - Classifications: {}".format(
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
            flags['QUESTION_DELIMITER'].join(
                [flags['QUESTION_PREFIX'], question]))

    logger.info("Automatically generated question header: {}".format(
        question_header))

    logger.info("Automatically generated cleaned question header: {}".format(
        question_header_print))

    ######################################
    # Export
    ######################################

    # build csv header
    classification_header_cols = flags['CLASSIFICATION_INFO_TO_ADD']
    classification_header_cols = [
        flags['CLASSIFICATION_INFO_MAPPER'][x] if x
        in flags['CLASSIFICATION_INFO_MAPPER'] else x for
        x in classification_header_cols]

    subject_header_cols = flags['SUBJECT_INFO_TO_ADD']
    subject_header_cols = [
        flags['SUBJECT_INFO_MAPPER'][x] if x
        in flags['SUBJECT_INFO_MAPPER'] else x for
        x in subject_header_cols]

    header = subject_header_cols + classification_header_cols + \
        question_header_print

    logger.info("Automatically generated output header: {}".format(
        header))

    with open(args['output_csv'], 'w') as f:
        csv_writer = csv.writer(f, delimiter=',')
        logger.info("Writing output to {}".format(args['output_csv']))
        csv_writer.writerow(header)
        tot = len(all_records)
        for line_no, record in enumerate(all_records):
            # get subject info data
            subject_data = [record[x] for x in subject_header_cols]
            # get classification info data
            class_data = [record[x] for x in classification_header_cols]
            # get annotation info data
            answers = extractor.flatten_annotations(
                record['annos'], question_types,  question_answers)
            answers_ordered = [
                answers[x] if x in answers else '' for x
                in question_header]
            csv_writer.writerow(subject_data + class_data + answers_ordered)
        logger.info("Wrote {} records to {}".format(
            line_no, args['output_csv']))
