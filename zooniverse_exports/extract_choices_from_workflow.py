""" Extract all possible choices of a workflow csv
    Only considers the most recent workflow version
"""
import csv
import json
import argparse

# args = dict()
# args['workflow_csv'] = 'D:\Studium_GD\Zooniverse\SnapshotSafari\data\zooniverse_exports\RUA\workflows.csv'
# args['output'] = 'D:\Studium_GD\Zooniverse\SnapshotSafari\data\zooniverse_exports\RUA\label_mapping.json'


if __name__ == '__main__':

    # Parse command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("-workflow_csv", type=str, required=True)
    parser.add_argument("-output", type=str, required=True)

    args = vars(parser.parse_args())

    lines = list()
    with open(args['workflow_csv'], "r", encoding="utf-8") as ins:
        csv_reader = csv.reader(ins, delimiter=',')
        for _id, line in enumerate(csv_reader):
            if _id == 0:
                row_name_to_id_mapper = {x: i for i, x in enumerate(line)}
                row_id_to_name_mapper = {i: x for i, x in enumerate(line)}
            else:
                lines.append(line)

    # get tasks of most recent workflow
    tasks = lines[0][row_name_to_id_mapper['tasks']]
    tasks = json.loads(tasks)

    # get all species choices and build a mapping file
    species = tasks['T0']['choices'].keys()

    species = list(species)
    species.sort()

    # remove 'NOTHINGHERE'
    if 'NOTHINGHERE' in species:
        species.remove('NOTHINGHERE')

    species_to_id_map = {v: k for k, v in enumerate(species)}
    id_to_species_map = {v: k for k, v in species_to_id_map.items()}

    # export the species to id mapping
    with open(args['output'], 'w') as fp:
        json.dump(species_to_id_map, fp)
