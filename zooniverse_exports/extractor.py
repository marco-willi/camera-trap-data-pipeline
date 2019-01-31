""" Functions to Extract Zooniverse classifications """
import json
import copy


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


def extract_annotations_from_json(line, mapper):
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
    json_annos = line[mapper['annotations']]
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
