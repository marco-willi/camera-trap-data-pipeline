""" Get Zooniverse Data using the Panoptes Client """
import argparse
import csv
import logging

from panoptes_client import Project, Panoptes

from utils.utils import read_config_file, set_file_permission
from utils.logger import set_logging


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
    parser.add_argument("--generate_new_export", action='store_true')
    parser.add_argument("--log_dir", type=str, default=None)
    parser.add_argument(
        "--log_filename", type=str, default='get_zooniverse_export')

    args = vars(parser.parse_args())

    # logging
    set_logging(args['log_dir'], args['log_filename'])
    logger = logging.getLogger(__name__)

    # get Zooniverse passowrd
    config = read_config_file(args['password_file'])

    # connect to panoptes
    Panoptes.connect(username=config['zooniverse']['username'],
                     password=config['zooniverse']['password'])

    # Get Project
    my_project = Project(args['project_id'])

    logger.info("Getting Data for Project id %s - %s" %
                (args['project_id'], my_project.display_name))

    # generate new export and wait until it is ready
    if args['generate_new_export']:
        logger.info("Generating new export and wait until it is ready")
        my_project.wait_export(args['export_type'])

    # get info about export
    export_description = my_project.describe_export(args['export_type'])
    export_description['meta']['media']['page_size']

    export = my_project.get_export(args['export_type'])

    # save classifications to csv file
    logger.info("Starting to write file %s" % args['output_file'])
    with open(args['output_file'], 'w', newline='') as csvfile:
        writer = csv.writer(csvfile, delimiter=',')
        for i, row in enumerate(export.csv_reader()):
            writer.writerow(row)
            if (i % 10000) == 0:
                print("Wrote %s records" % i)

    logger.info("Finished Writing File %s - Wrote %s records" %
                (args['output_file'], i))

    set_file_permission(args['output_file'])
