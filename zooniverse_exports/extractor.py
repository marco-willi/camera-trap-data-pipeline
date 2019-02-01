""" Functions to Extract Zooniverse classifications
    - extraction comprises the analysis of Zooniverse exports to
      clean and extract relevant information
    - Zooniverse exports are csvs with nested json structures which capture
      the complexity of volunteer tasks
"""
import json
import copy
import logging

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
    Input: {'task': 'T0', 'value':
            [{'choice': 'GAZELLEGRANTS',
              'answers': {'HOWMANY': '1',
                          'WHATBEHAVIORSDOYOUSEE': ['STANDING'],
                          'ARETHEREANYYOUNGPRESENT': 'NO'},
              'filters': {}
              }
    Output:
        [[{'howmany': '1'},
          {'whatbehaviorsdoyousee': ['standing']},
          {'arethereanyyoungpresent': 'no'},
          {'choice': 'gazellegrants'}]]
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
            raise ValueError("task_type %s unknown" % task_type)
        extractions.append(extracted)
    return extractions


def map_task_questions(answers_list, flags):
    """ Map Questions
        Input:  [{'howmany': '1'}, ...]
        Output: [{'count': '1'}, ... ]
    """
    answers_list_mapped = copy.deepcopy(answers_list)
    for i, question_answer in enumerate(answers_list):
        for question, answers in question_answer.items():
            if question in flags['QUESTION_NAME_MAPPER']:
                map_question = flags['QUESTION_NAME_MAPPER'][question]
                answers_list_mapped[i][map_question] = answers
                answers_list_mapped[i].pop(question, None)
                if map_question in flags['ANSWER_TYPE_MAPPER']:
                    answer_mapper = flags['ANSWER_TYPE_MAPPER'][map_question]
                    map_answers = map_task_answers(answers, answer_mapper)
                    answers_list_mapped[i][map_question] = map_answers
            elif question in flags['ANSWER_TYPE_MAPPER']:
                answer_mapper = flags['ANSWER_TYPE_MAPPER'][question]
                map_answers = map_task_answers(answers, answer_mapper)
                answers_list_mapped[i][question] = map_answers
    return answers_list_mapped


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
        if mapper[cond_key] is not cond_val:
            return False
    return True


# build question_answer pairs
def analyze_question_types(all_records):
    """ Analyze annotations to determine question types
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


def define_question_answers(all_records):
    """ Analyze annotations to determine question and answer mappings
        Output:
         {'species': ['vulture', 'zebra', 'nyala', ...],
          'young_present': ['yes', 'no'],
          }
    """
    question_answers = dict()
    for record in all_records:
        annos = record['annos']
        for anno in annos:
            for question, answers in anno.items():
                if question not in question_answers:
                    question_answers[question] = set()
                if isinstance(answers, str):
                    question_answers[question].add(answers)
                elif isinstance(answers, list):
                    for answer in answers:
                        question_answers[question].add(answer)
    return {k: list(v) for k, v in question_answers.items()}


def build_question_header(question_answers, question_types):
    """ Build a header based on question type an answers
        Output: ['species', 'count', 'eating', 'interacting',
                 'moving', 'resting', 'standing',
                 'young_present', 'horns_visible']
    """
    question_header = list()
    for k, v in question_answers.items():
        if question_types[k] == 'single':
            question_header.append(k)
        else:
            sub_answers = [x for x in v]
            sub_answers.sort()
            question_header += sub_answers
    return question_header


def flatten_annotations(annotations, question_types, question_answers):
    """ Unpack / Flatten Annotations
    Input: [{'species': 'zebra', 'whatbehaviorsdoyousee':
            ['standing', 'resting']}]
    Output: {'species': 'zebra',
            'standing': '1', 'resting': '1', 'moving': '0', ...}
    """
    flattened = dict()
    for question_answer in annotations:
        for question, answers in question_answer.items():
            if question_types[question] == 'multi':
                for choice in question_answers[question]:
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
