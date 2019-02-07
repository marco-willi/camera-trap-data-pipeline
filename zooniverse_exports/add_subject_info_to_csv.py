""" Add Subject info to export
    - join subject-information via subject_id
    - Raw Subject-Data Example:
    subject_id,project_id,workflow_id,subject_set_id,metadata,locations,classifications_count,retired_at,retirement_reason,created_at,updated_at
        17510222,5115,4979,18231,"{""#roll"":1,""#site"":""J04"",
            ""Image 1"":""6562_6082_5649.JPG"",
            ""Image 2"":""6116_9310_6586.JPG"",
            ""Image 3"":""4600_9071_9361.JPG"",
            ""license"":""SnapshotSafari"",""#capture"":6,
            ""attribution"":""University of Minnesota Lion Center +
                SnapshotSafari + Singita Grumeti""}",
            "{""0"":""https://panoptes-uploads.zooniverse.org/production/subject_location/f26d4b0a-81f8-4203-bd90-c85d659a05bb.jpeg"",
              ""1"":""https://panoptes-uploads.zooniverse.org/production/subject_location/16f9fa0f-95b1-4425-9d27-55878a33f39e.jpeg"",
              ""2"":""https://panoptes-uploads.zooniverse.org/production/subject_location/7ed39f2d-70b4-4d5e-ae1a-29215832a47e.jpeg""}",
              17,2018-11-13 08:17:58 UTC,consensus,2018-01-28 02:27:23 UTC,2018-01-28 02:27:23 UTC
"""
import csv
import os
import logging
import argparse

from logger import setup_logger, create_logfile_name


if __name__ == '__main__':

    # Parse command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("--input_csv", type=str, required=True)
    parser.add_argument("--subject_csv", type=str, required=True)
    parser.add_argument("--output_csv", type=str, required=False, default=None)

    args = vars(parser.parse_args())

    ######################################
    # Check Input
    ######################################

    if not os.path.isfile(args['input_csv']):
        raise FileNotFoundError("input_csv: {} not found".format(
                                args['input_csv']))

    if not os.path.isfile(args['subject_csv']):
        raise FileNotFoundError("subject_csv: {} not found".format(
                                args['subject_csv']))

    if args['output_csv'] is None:
        args['output_csv'] = args['input_csv']

    ######################################
    # Configuration
    ######################################

    log_file_name = create_logfile_name('add_subject_info')
    log_file_path = os.path.join(
        os.path.dirname(args['output_csv']), log_file_name)
    setup_logger(log_file_path)
    logger = logging.getLogger(__name__)

    for k, v in args.items():
        logger.info("Argument {}: {}".format(k, v))

    # Read Subject CSV
    subject_info = dict()
    with open(args['subject_csv'], "r") as ins:
        csv_reader = csv.reader(ins, delimiter=',', quotechar='"')
        header_subject = next(csv_reader)
        row_name_to_id_mapper_sub = {x: i for i, x in enumerate(header_subject)}
        for line_no, line in enumerate(csv_reader):
            subject_id = line[row_name_to_id_mapper_sub['subject_id']]
            subject_info[subject_id] = line

    # Read Input CSV with subject_id column
    combined_data = list()
    with open(args['input_csv'], "r") as ins:
        csv_reader = csv.reader(ins, delimiter=',', quotechar='"')
        header = next(csv_reader)
        row_name_to_id_mapper = {x: i for i, x in enumerate(header)}
        for line_no, line in enumerate(csv_reader):
            # print status
            if ((line_no % 10000) == 0) and (line_no > 0):
                print("Processed {:,} records".format(line_no))
            subject_id = line[row_name_to_id_mapper['subject_id']]
            # get subject_info
            subject_info_current = subject_info[subject_id]
            # input info
            combined_info = {
                **subject_info_current,
                **{k: line[v] for k, v in row_name_to_id_mapper.items()}
                }
            combined_data.append(combined_info)

    # duplicate subject_id
    header_no_subject = [x for x in header if x is not 'subject_id']
    output_header = header_subject + header_no_subject

    # Output all combined records
    with open(args['output_csv'], 'w') as f:
        csv_writer = csv.writer(f, delimiter=',')
        logger.info("Writing output to {}".format(args['output_csv']))
        csv_writer.writerow(output_header)
        tot = len(combined_data)
        for line_no, record in enumerate(combined_data):
            # get subject info data
            to_write = [record[x] for x in output_header]
            csv_writer.writerow(to_write)
            # print status
            if ((line_no % 10000) == 0) and (line_no > 0):
                print("Wrote {:,} records".format(line_no))
        logger.info("Wrote {} records to {}".format(
            line_no, args['output_csv']))
