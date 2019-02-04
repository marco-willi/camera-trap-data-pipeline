""" Get Zooniverse Data using the Panoptes Client """
import argparse
import csv
import os

from panoptes_client import Project, Panoptes

from utils import read_config_file


if __name__ == '__main__':

    # Parse command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--password_file", type=str, required=True,
        help="File that contains the Zooniverse password (.ini),\
              Example File:\
              [zooniverse]\
              username: dummy\
              password: 1234")
    parser.add_argument("--project_id", type=int, required=True)
    parser.add_argument("--output_file", type=str, required=True)
    parser.add_argument("--export_type", default='classifications',
                        type=str, required=False)
    parser.add_argument("--new_export", default=0, type=int, required=False)

    args = vars(parser.parse_args())

    # get Zooniverse passowrd
    config = read_config_file(args['password_file'])

    # connect to panoptes
    Panoptes.connect(username=config['zooniverse']['username'],
                     password=config['zooniverse']['password'])

    # Get Project
    my_project = Project(args['project_id'])

    print("Getting Data for Project id %s - %s" %
          (args['project_id'], my_project.display_name))

    # generate new export and wait until it is ready
    if args['new_export']:
        print("Generating new export and wait until it is ready")
        my_project.wait_export(args['export_type'])

    # get info about export
    export_description = my_project.describe_export(args['export_type'])
    export_description['meta']['media']['page_size']

    export = my_project.get_export(args['export_type'])

    # save classifications to csv file
    print("Starting to write file %s" % args['output_file'])
    with open(args['output_file'], 'w', newline='') as csvfile:
        writer = csv.writer(csvfile, delimiter=',')
        for i, row in enumerate(export.csv_reader()):
            writer.writerow(row)
            if (i % 10000) == 0:
                print("Wrote %s records" % i)

    print("Finished Writing File %s - Wrote %s records" %
          (args['output_file'], i))

    os.chmod(args['output_file'], 0o660)
