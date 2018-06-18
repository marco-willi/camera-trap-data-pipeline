""" Extract Snapshot Safari Classifications

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
from collections import OrderedDict
from collections import Counter
import traceback

from utils import print_progress


if __name__ == '__main__':

    # Parse command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("-classification_csv", type=str, required=True)
    parser.add_argument("-output_csv", type=str, required=True)
    parser.add_argument("-workflow_id", type=str, required=True)
    parser.add_argument("-workflow_version", type=str, required=True)

    args = vars(parser.parse_args())

    input_file = args['classification_csv']
    output_file = args['output_csv']
    workflow_id = args['workflow_id']
    workflow_version_major = args['workflow_version'].split('.')[0]

    # input_file = "D:\\Studium_GD\\Zooniverse\\SnapshotSafari\\data\\zooniverse_exports\\GRU\\classifications_sampled.csv"
    # output_file = "D:\\Studium_GD\\Zooniverse\\SnapshotSafari\\data\\zooniverse_exports\\GRU\\classifications_extracted_sampled.csv"
    # workflow_id = '4979'
    # workflow_version_major = '275'

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

    def extract_t1_task(task_value, default=snapshot_safari_default_record):
        """ Extract T1 task (shortcut task) """
        value = task_value['value'][0]
        default['species'] = value
        return default

    def extract_t0_task(task_value, default=snapshot_safari_default_record):
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

        if isinstance(task_values[0], list):
            return len(task_values[0])
        else:
            return len(task_values)

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
                    print(traceback.format_exc())
                    break

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
