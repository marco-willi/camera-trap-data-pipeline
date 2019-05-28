""" Functions to Extract Zooniverse classifications
    - extraction comprises the analysis of Zooniverse exports to
      clean and extract relevant information
    - Zooniverse exports are csvs with nested json structures which capture
      the complexity of volunteer tasks
"""
import json
import copy
import logging
from datetime import datetime
from collections import defaultdict, Counter

logger = logging.getLogger(__name__)


def identify_task_type(task_data):
    """ Identify task type - survey or question task """
    if 'choice' in task_data:
        return 'survey_task'
    elif 'value' in task_data:
        values = task_data['value']
        if isinstance(values, list):
            if any(['choice' in x for x in values]):
                return 'survey_task'
        return 'question_task'
    else:
        raise ValueError("task_type not identifiable %s" % task_data)


def task_is_completed(task):
    """ Check if task has been completed
    Input:
        {'value': [{'choice': 'GAZELLEGRANTS',..}]}
    """
    return len(task['value']) > 0


def extract_key_from_json(line, key, mapper):
    """ Convert annotations to list
    Input: list with Json string
    Output:
        [{'task': 'T0', 'value':
         [{'choice': 'GAZELLEGRANTS',
           'answers': {'HOWMANY': '1', 'WHATBEHAVIORSDOYOUSEE': ['STANDING'],
                       'ARETHEREANYYOUNGPRESENT': 'NO'},
           'filters': {}
           }]
        }]
    """
    json_annos = line[mapper[key]]
    dict_annos = json.loads(json_annos)
    return dict_annos


def extract_survey_task(survey_task, flags):
    """ Extract Identification from Survey Task
    Input: {"choice": "GIRAFFE",
                       "answers":{"HOWMANY":"5",
                              "WHATBEHAVIORSDOYOUSEE":["EATING", "MOVING"],
                              "ARETHEREANYYOUNGPRESENT":"NO"}}
    Output:
        [{'howmany': '5'},
         {'whatbehaviorsdoyousee': ['eating', 'moving']},
         {'arethereanyyoungpresent': 'no'},
         {'choice': 'giraffe'}]
    """
    results = list()
    choice = survey_task['choice'].lower()
    if len(survey_task['answers'].keys()) > 0:
        for question, answers in survey_task['answers'].items():
            if question.lower() in flags['QUESTIONS_TO_IGNORE']:
                continue
            if isinstance(answers, list):
                res = {question.lower(): list()}
                for answer in answers:
                    res[question.lower()].append(answer.lower())
                results.append(res)
            else:
                res = {question.lower(): answers.lower()}
                results.append(res)
    results.append({'choice': choice})
    return results


def extract_question_task(question_task):
    """ Extract question tasks """
    if isinstance(question_task, list):
        answers = [x.lower() for x in question_task]
    else:
        answers = question_task.lower()
    return [{'question': answers}]


def extract_task_info(task, task_type, flags):
    """ Extract task information
        - handles different task types
    """
    task_value = task['value']
    extractions = list()
    if not isinstance(task_value, list):
        task_value = [task_value]
    for task_id_answer in task_value:
        if task_type == 'survey_task':
            extracted = extract_survey_task(task_id_answer, flags)
        elif task_type == 'question_task':
            extracted = extract_question_task(task_id_answer)
        else:
            logger.error("task_type {} unknown, found in {}".format(
                task_type, task_id_answer))
            raise ValueError("task_type %s unknown" % task_type)
        extractions.append(extracted)
    return extractions


def map_task_questions(answers_list, flags):
    """ Map Questions
        Input:
            - [{'howmany': '1'}, {'species': 'zebra_large'},
               {'young_present': 'no'}, ...]
            - flags['QUESTION_NAME_MAPPER']:
                {'howmany': 'count'}
            - flags['ANSWER_TYPE_MAPPER']:
                {'species': {'zebra_large': 'zebra'}}
            - flags['ANSWER_MAPPER']: {'no': '0', ..}
        Output: [{'count': '1'}, {'young_present': '0'}, {'species': 'zebra'}]
    """
    answers_list_mapped = copy.deepcopy(answers_list)
    # 1) map question names
    for i, question_answer in enumerate(answers_list):
        for question, answers in question_answer.items():
            if question in flags['QUESTION_NAME_MAPPER']:
                map_question = flags['QUESTION_NAME_MAPPER'][question]
                answers_list_mapped[i][map_question] = answers
                answers_list_mapped[i].pop(question, None)
    # 2) Map answers based on mapped question names
    answers_list_mapped_2 = copy.deepcopy(answers_list_mapped)
    for i, question_answer in enumerate(answers_list_mapped_2):
        for question, answers in question_answer.items():
            # map specific questions
            if question in flags['ANSWER_TYPE_MAPPER']:
                answer_mapper = flags['ANSWER_TYPE_MAPPER'][question]
                map_answers = map_task_answers(answers, answer_mapper)
                answers_list_mapped_2[i][question] = map_answers
            # mapp all answers globally
            answers_updated = answers_list_mapped_2[i][question]
            answers_list_mapped_2[i][question] = \
                map_task_answers(answers_updated, flags['ANSWER_MAPPER'])
    return answers_list_mapped_2


def map_task_answers(answers, map):
    """ Map Task Answers
    """
    if isinstance(answers, str):
        if answers.lower() in map:
            return map[answers]
    elif isinstance(answers, list):
        lower_case = [x.lower() for x in answers]
        mapped = [x if x not in map else map[x] for x in lower_case]
        return mapped
    return answers


def extract_classification_info(line, row_name_to_id_mapper, flags):
    """ Extract info on classification level """
    res = {x: line[row_name_to_id_mapper[x]] for x in
           flags['CLASSIFICATION_INFO_TO_ADD']}
    return res


def is_eligible(line, mapper, cond):
    """ Check whether classification is eligible
    cond: {'workflow_id': '345'}
    """
    for cond_key, cond_val in cond.items():
        if line[mapper[cond_key]] != cond_val:
            return False
    return True


def get_season_from_subject_data(subject_data, subject_id):
    try:
        data = subject_data[subject_id]
        return data['#season']
    except KeyError:
        logger.warning(
            "'#season' field could not be extracted for subject_id: {}- returning '' as season".format(subject_id))
        return ''


def project_is_live(metadata):
    try:
        return metadata['live_project']
    except KeyError:
        logger.warning(
            "'live_project' status could not be extracted - returning True")
        return True


def get_workflow_major_version(workflow_version):
    """ Get major version number of a workflow_version
        Input: 743.34
        Output: 743
    """
    if '.' in workflow_version:
        return workflow_version.split('.')[0]
    else:
        return workflow_version


def _convert_utc_str_to_datetime(date_str):
    date, time, utc = date_str.split(' ')
    return datetime.strptime(date, "%Y-%m-%d")


def convert_date_str_to_datetime(date):
    """ Check if date is valid """
    return datetime.strptime(date, "%Y-%m-%d")


def is_in_date_range(
        cls_dict,
        no_earlier_than_date=None,
        no_later_than_date=None):
    """ Check whether classification was made within the specified dates """
    if (no_earlier_than_date is None) and (no_later_than_date is None):
        return True
    date_str = cls_dict['created_at']
    try:
        date = _convert_utc_str_to_datetime(date_str)
    except:
        logger.debug(
            "Failed to extract 'created_at': {} to datetime".format(date_str))
        return True
    if no_earlier_than_date is not None:
        is_not_too_early = (date >= no_earlier_than_date)
    else:
        is_not_too_early = True
    if no_later_than_date is not None:
        is_not_too_late = (date <= no_later_than_date)
    else:
        is_not_too_late = True
    return (is_not_too_late and is_not_too_early)


def is_eligible_workflow(
        cls_dict,
        workflow_id=None,
        workflow_version_min=None):
    """ Check whether classification is in an eligible workflow
        For the workflow version, only the major version is checked, e.g.,
        586.16, only 586 is checked for
    Input:
        cls_dict: dict of classification
        workflow_id: str indicating the workflow
        workflow_version_min: str indicating the minimum workflow_version
    """
    # Return True if no workflow_id specified
    if workflow_id is None:
        if workflow_version_min is not None:
            logger.warning(
                "Specified workflow_version_min but no workflow_id")
        return True

    # extract data
    actual_workflow_version = get_workflow_major_version(
        cls_dict['workflow_version'])
    actual_workflow_id = cls_dict['workflow_id']

    # check workflow id
    if actual_workflow_id != workflow_id:
        return False

    # check workflow version min
    if workflow_version_min is not None:
        workflow_version_min = get_workflow_major_version(
            workflow_version_min)
        if int(actual_workflow_version) >= int(workflow_version_min):
            return True
        else:
            return False
    else:
        return True


# build question_answer pairs
def analyze_question_types(all_records):
    """ Analyze annotations to determine question types
        Input: - List with all Zooniverse records
        Output: {'species': 'single',
                 'whatbehaviorsdoyousee': 'multi'}
    """
    question_types = dict()
    for record in all_records:
        annos = record['annos']
        for anno in annos:
            for question, answers in anno.items():
                if isinstance(answers, str):
                    question_types[question] = 'single'
                elif isinstance(answers, list):
                    question_types[question] = 'multi'
    return question_types


def deduplicate_answers(classification_answers, flags):
    """ De-duplicate multiple identical answers in the same classification
        This only happens if there are two or more tasks that allow for the
        same answer: typically 'blank' annotations
        Input: [[{'count': '1'}, {'whatbehaviorsdoyousee': ['resting']},
                 {'young_present': '0'}, {'species': 'blank'}],
                [{'species': 'blank'}]]
        Output: [[{'count': '1'}, {'whatbehaviorsdoyousee': ['resting']},
                 {'young_present': '0'}, {'species': 'blank'}]]
    """
    # define on which question/key to de-duplicate
    try:
        primary_question = flags['QUESTION_NAME_MAPPER']['choice']
    except:
        primary_question = 'choice'
    deduplicated = list()
    primary_used = set()
    for i, task_answers in enumerate(classification_answers):
        # get primary answer of current choice
        primary_current = [x for x in task_answers if primary_question in x]
        primary_answer = primary_current[0][primary_question]
        if primary_answer not in primary_used:
            deduplicated.append(task_answers)
            primary_used.add(primary_answer)
        else:
            logger.debug("Removed duplicate answer: {}".format(
                classification_answers))
    return deduplicated


def find_question_answer_pairs(all_records):
    """ Analyze annotations to determine question and answer mappings
        Output:
         {'species': ['vulture', 'zebra', 'nyala', ...],
          'young_present': ['yes', 'no'],
          }
    """
    pairs = defaultdict(Counter)
    for record in all_records:
        annos = record['annos']
        for anno in annos:
            for question, answers in anno.items():
                if isinstance(answers, list):
                    pairs[question].update(answers)
                else:
                    pairs[question].update({answers})
    return {k: list(v.keys()) for k, v in pairs.items()}


def build_question_header(question_answer_pairs, question_types):
    """ Build a header based on question type an answers
        Output: ['species', 'count', 'eating', 'interacting',
                 'moving', 'resting', 'standing',
                 'young_present', 'horns_visible']
    """
    question_header = list()
    for k, v in question_answer_pairs.items():
        if question_types[k] == 'single':
            question_header.append(k)
        else:
            sub_answers = [x for x in v]
            sub_answers.sort()
            question_header += sub_answers
    return question_header


def flatten_annotations(
        annotations,
        question_types,
        possible_multi_question_answers):
    """ Unpack / Flatten Annotations - add 0 to multi-answer questions
    Input:
        - possible_question_answers
            {'whatbehaviorsdoyousee': ['standing', 'resting', 'moving',...]}
        - question_types:
            {'species': 'single', 'whatbehaviorsdoyousee': 'multi'}
        - annotations:
            [{'species': 'zebra', 'whatbehaviorsdoyousee':
             ['standing', 'resting']}]
    Output: {'species': 'zebra',
            'standing': '1', 'resting': '1', 'moving': '0', ...}
    """
    flattened = dict()
    for question_answer in annotations:
        for question, answers in question_answer.items():
            if question_types[question] == 'multi':
                for choice in possible_multi_question_answers[question]:
                    if choice in answers:
                        flattened[choice] = '1'
                    else:
                        flattened[choice] = '0'
            else:
                flattened[question] = answers
    return flattened


def rename_dict_keys(input, map):
    """ Rename keys of a dict
    Example:
        input: {'a': 1, 'b':2}, map: {'a': 'aa'}
        output: {'aa': 1, 'b': 2}
    """
    output = dict()
    for k, v in input.items():
        if k in map:
            output[map[k]] = v
        else:
            output[k] = v
    return output


def classification_is_valid(cls_dict):
    """ Check all required fields are available """
    required = [
        'user_name', 'subject_ids', 'subject_data', 'annotations',
        'workflow_id', 'workflow_version', 'created_at',
        'classification_id']
    if not all([x in cls_dict for x in required]):
        return False
    else:
        return True


def subject_already_seen(cls_dict):
    """ Determine if subject was already seen """
    meta_data = json.loads(cls_dict['metadata'])
    if 'see_before' in meta_data:
        return meta_data['seen_before']
    elif 'subject_selection_state' in meta_data:
        try:
            return meta_data['subject_selection_state']['already_seen']
        except KeyError:
            return False
    else:
        return False


def get_classification_unqiue_key(cls_dict):
    """ Return unique key of classification """
    return (cls_dict['user_name'],
            cls_dict['subject_ids'],
            cls_dict['workflow_id'])


def classification_is_duplicate(cls_dict, tracker):
    unique_key = get_classification_unqiue_key(cls_dict)
    if unique_key in tracker:
        return True
    else:
        tracker.add(unique_key)
        return False
