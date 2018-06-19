""" Generate a Prediction File from Files that contain the path to images for
    a machine classifier
"""
import csv
import os
import argparse

if __name__ == '__main__':

    # Parse command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("-root_path", type=str, required=True)
    parser.add_argument("-files", nargs='+', type=str, required=True)
    parser.add_argument("-path_field", type=str, default="path")
    parser.add_argument("-output_file", type=str, required=True)

    args = vars(parser.parse_args())

    file_rows = list()
    for file in args['files']:
        full_path = os.path.join(args['root_path'], file)
        with open(full_path, newline='') as csvfile:
            reader = csv.reader(csvfile, delimiter=',')
            for row_id, row in enumerate(reader):
                if row_id == 0:
                    header = row
                    name_to_id_mapping = {x: i for i, x in enumerate(header)}
                    continue
                else:
                    path = row[name_to_id_mapping[args['path_field']]]
                    file_rows.append([path])

    with open(args['output_file'], "w", newline='') as outs:
        csv_writer = csv.writer(outs, delimiter=',')
        print("Writing file to %s" % args['output_file'])
        for i, line in enumerate(file_rows):
            csv_writer.writerow(line)
