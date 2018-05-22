""" Get Zooniverse Data using the Panoptes Client

    Example Usage:
    --------------
    python3 get_zooniverse_export.py -username user -password 1234 \
            -project_id 4715 \
            -output_file classifications.csv \
            -export_type classifications \
            -new_export 0
"""
import argparse
import csv

from panoptes_client import Project, Panoptes


if __name__ == '__main__':

    # Parse command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("-username", type=str, required=True)
    parser.add_argument("-password", type=str, required=True)
    parser.add_argument("-project_id", type=int, required=True)
    parser.add_argument("-output_file", type=str, required=True)
    parser.add_argument("-export_type", default='classifications',
                        type=str, required=False)
    parser.add_argument("-new_export", default=0, type=int, required=False)

    args = vars(parser.parse_args())

    # connect to panoptes
    Panoptes.connect(username=args['username'], password=args['password'])

    # Get Project
    my_project = Project(args['project_id'])

    print("Getting Data for Project id %s - %s" %
          (args['project_id'], my_project.display_name))

    # get classifications
    if args['new_export']:
        my_project.generate_export('classifications')

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
