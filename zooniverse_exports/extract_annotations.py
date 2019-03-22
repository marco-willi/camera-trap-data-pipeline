""" Extract Zooniverse Classifications
    - Extract annotations from classifications
    - Export to csv file
        Output Example Header:
            user_name,user_id,created_at,subject_id,workflow_id,
            workflow_version,
            classification_id,retirement_reason,retired_at,question__count,
            question__eating,question__interacting,question__moving,
            question__resting,question__standing,question__young_present,
            question__species,question__horns_visible
        Output Example Record:
            not-logged-in-4ee662baaa306798b359,,2018-02-06 17:09:43 UTC,
            17530583,4979,275.13,88921948,consensus,2018-11-21T19:16:34.362Z,
            4,0,1,0,0,1,1,wildebeest,
"""
import csv
from collections import Counter
import traceback
import os
import argparse
import logging
import textwrap

from logger import setup_logger, create_log_file
from zooniverse_exports import extractor
from utils import print_nested_dict, set_file_permission
from config.cfg import cfg


flags = cfg['extractor_flags']

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
# args['classification_csv'] = '/home/packerc/shared/zooniverse/Exports/MTZ/MTZ_S1_classifications.csv'
# args['output_csv'] = '/home/packerc/shared/zooniverse/Exports/MTZ/MTZ_S1_annotations_test.csv'
# args['workflow_id'] = None
# args['workflow_version'] = None
# args['workflow_version_min'] = None


if __name__ == '__main__':

    # Parse command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("--classification_csv", type=str, required=True)
    parser.add_argument("--output_csv", type=str, required=True)
    parser.add_argument(
        "--log_dir", type=str, default=None)
    parser.add_argument(
        "--log_filename", type=str,
        default='extract_annotations')
    parser.add_argument(
        "--workflow_id", type=str, default=None,
        help="Extract only classifications from the specified workflow_id")
    parser.add_argument(
        "--workflow_version", type=str, default=None,
        help="Extract only classifications from the specified workflow \
        version. Only the major version number is compared, e.g., \
        version 45.12 is identical to 45.45")
    parser.add_argument(
        "--workflow_version_min", type=str, default=None,
        help="Extract only classifications with at least the speciefied \
        workflow version number \
        version. Only the major version number is compared, e.g., \
        version 45.12 is identical to 45.45")

    args = vars(parser.parse_args())

    ######################################
    # Check Input
    ######################################

    if not os.path.isfile(args['classification_csv']):
        raise FileNotFoundError("classification_csv: {} not found".format(
                                args['classification_csv']))

    at_least_one_none = [
        args['workflow_version'], args['workflow_version_min']]
    assert any([x is None for x in at_least_one_none]), \
        "One of {} must be None".format(at_least_one_none)

    ######################################
    # Configuration
    ######################################

    # logging
    if args['log_dir'] is not None:
        log_file_path = create_log_file(args['log_dir'], args['log_filename'])
        setup_logger(log_file_path)
    else:
        setup_logger()
    logger = logging.getLogger(__name__)

    for k, v in args.items():
        logger.info("Argument {}: {}".format(k, v))

    # logging flags
    print_nested_dict('', flags)

    ######################################
    # Read and Process Classifications
    ######################################

    all_records = list()
    n_incomplete_tasks = 0
    n_seen_before = 0
    n_exceptions = 0
    n_duplicate_subject_by_same_user = 0
    n_not_eligible_workflow = 0
    user_subject_dict = dict()
    with open(args['classification_csv'], "r") as ins:
        csv_reader = csv.reader(ins, delimiter=',', quotechar='"')
        header = next(csv_reader)
        row_name_to_id_mapper = {x: i for i, x in enumerate(header)}
        for line_no, line in enumerate(csv_reader):
            # print status
            if ((line_no % 10000) == 0) and (line_no > 0):
                print("Processed {:,} classifications".format(line_no))
            # check eligibility of classification
            is_eligible_workflow = extractor.is_eligible_workflow(
                line, row_name_to_id_mapper,
                args['workflow_id'],
                args['workflow_version'],
                args['workflow_version_min'])
            if not is_eligible_workflow:
                n_not_eligible_workflow += 1
                continue
            try:
                # extract classification-level info
                classification_info = extractor.extract_classification_info(
                    line, row_name_to_id_mapper, flags)
                # map classification info header
                classification_info = extractor.rename_dict_keys(
                    classification_info, flags['CLASSIFICATION_INFO_MAPPER'])
                # extract Zooniverse subject metadata
                subject_zooniverse_metadata = extractor.extract_key_from_json(
                    line, 'metadata', row_name_to_id_mapper
                    )
                # if subject was flagged as 'seen_before' skip it
                try:
                    if subject_zooniverse_metadata['seen_before']:
                        if n_seen_before < 10:
                            msg = "Removed classification_id: {} due to \
                                   'seen_before' flag".format(
                                 classification_info['classification_id'])
                            logger.debug(textwrap.shorten(msg, width=99))
                        elif n_seen_before == 10:
                            logger.debug("Stop printing 'seen_before' msgs..")
                        n_seen_before += 1
                        continue
                except:
                    pass
                # check if subject was already classified by user
                # if so, skip it
                try:
                    user_name = classification_info['user_name']
                    subject_id = classification_info['subject_id']
                    if user_name not in user_subject_dict:
                        user_subject_dict[user_name] = set()
                    if subject_id in user_subject_dict[user_name]:
                        msg = "Removed classification_id: {} due \
                               to subject_id {} already classified by \
                               user {}".format(
                         classification_info['classification_id'],
                         subject_id, user_name)
                        logger.debug(textwrap.shorten(msg, width=99))
                        n_duplicate_subject_by_same_user += 1
                        continue
                    user_subject_dict[user_name].add(subject_id)
                except:
                    pass
                # extract subject-level data / retirement info
                subject_info_raw = extractor.extract_key_from_json(
                    line, 'subject_data', row_name_to_id_mapper
                    )[classification_info['subject_id']]
                subject_info_to_add = dict()
                for field in flags['RETIREMENT_INFO_TO_ADD']:
                    try:
                        ret_info = subject_info_raw['retired'][field]
                        subject_info_to_add[field] = ret_info
                    except:
                        subject_info_to_add[field] = ''
                # get all annotations (list of annotations)
                annotations_list = extractor.extract_key_from_json(
                    line, 'annotations', row_name_to_id_mapper)
                # get all tasks of an annotation
                classification_answers = list()
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
                        classification_answers.append(_id_answer_mapped)
                # de-duplicate answers (example: two identical species
                # annotations from different tasks)
                classifications_deduplicated = extractor.deduplicate_answers(
                        classification_answers, flags)
                for classification_answer in classifications_deduplicated:
                    record = {**classification_info, **subject_info_to_add,
                              'annos': classification_answer}
                    all_records.append(record)
            except Exception:
                logger.warning("Error - Skipping Record %s" % line_no)
                logger.warning("Full line:\n %s" % line)
                logger.warning(traceback.format_exc())

    logger.info("Processed {:,} classifications".format(line_no))
    logger.info("Extracted {:,} identifications".format(len(all_records)))
    logger.info("Incomplete tasks: {:,}".format(n_incomplete_tasks))
    logger.info("Skipped due to 'seen_before' flag: {:,}".format(
        n_seen_before))
    logger.info("Skipped {:,} classifications due to prev. annot. by user".format(
        n_duplicate_subject_by_same_user))
    logger.info("Skipped {:,} classifications due to non-eligible workflow".format(
        n_not_eligible_workflow))
    logger.info("Skipped {:,} classifications due to unknown error".format(
        n_exceptions))

    ######################################
    # Analyse Classifications
    ######################################

    # Analyse the dataset
    question_stats = dict()
    user_stats = dict()
    not_logged_in_counter = 0
    workflow_stats = dict()
    retirement_stats = Counter()

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
        # get retirement stats
        if 'retirement_reason' in record:
            retirement_stats.update({record['retirement_reason']})
        # get workflow information
        if ('workflow_id' in record) and ('workflow_version' in record):
            wid = record['workflow_id']
            wv = record['workflow_version']
            if wid not in workflow_stats:
                workflow_stats[wid] = Counter()
            workflow_stats[wid].update([wv])
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
    for workflow_id, workflow_version_data in workflow_stats.items():
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

    # retirment reason stats
    if len(retirement_stats.keys()) > 0:
        logger.info("Retirement-Reason Stats:")
        total = sum([x for x in retirement_stats.values()])
        for answer, count in retirement_stats.most_common():
            logger.info("Retirement-Reason: {:20} -- counts: {:10} / {} ({:.2f} %)".format(
                answer, count, total, 100*count/total))

    ######################################
    # Unpack Classifications into
    # Annotations
    ######################################

    # get all possible answers to the questions
    question_answer_pairs = extractor.find_question_answer_pairs(all_records)

    # analyze the question types
    question_types = extractor.analyze_question_types(all_records)

    # build question header for csv export
    question_header = extractor.build_question_header(
        question_answer_pairs, question_types)

    # modify question column names as specified
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

    # build full csv header
    classification_header_cols = flags['CLASSIFICATION_INFO_TO_ADD']
    classification_header_cols = [
        flags['CLASSIFICATION_INFO_MAPPER'][x] if x
        in flags['CLASSIFICATION_INFO_MAPPER'] else x for
        x in classification_header_cols]

    retirement_header_cols = flags['RETIREMENT_INFO_TO_ADD']

    header = classification_header_cols + \
        retirement_header_cols + question_header_print

    logger.info("Automatically generated output header: {}".format(
        header))

    with open(args['output_csv'], 'w') as f:
        csv_writer = csv.writer(f, delimiter=',')
        logger.info("Writing output to {}".format(args['output_csv']))
        csv_writer.writerow(header)
        tot = len(all_records)
        for line_no, record in enumerate(all_records):
            # get retirement info data
            retirement_data = [record[x] for x in retirement_header_cols]
            # get classification info data
            class_data = [record[x] for x in classification_header_cols]
            # get annotation info data
            answers = extractor.flatten_annotations(
                record['annos'], question_types,  question_answer_pairs)
            answers_ordered = [
                answers[x] if x in answers else '' for x
                in question_header]
            csv_writer.writerow(
                class_data +
                retirement_data + answers_ordered)
        logger.info("Wrote {} annotations to {}".format(
            line_no, args['output_csv']))

    # change permmissions to read/write for group
    set_file_permission(args['output_csv'])
