""" Add Extracted Subject info to a CSV with subject_id column
"""
import csv
import os
import logging
import argparse

from logger import setup_logger, create_logfile_name

# args = dict()
# args['subject_csv'] = '/home/packerc/shared/zooniverse/Exports/CC/CC_S1_subjects_extracted.csv'
# args['input_csv'] = '/home/packerc/shared/zooniverse/Exports/CC/CC_S1_classifications_aggregated.csv'
# args['output_csv'] = '/home/packerc/shared/zooniverse/Exports/CC/CC_S1_classifications_aggregated_subject_info.csv'

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
            subject_dict = {
                k: line[v] for k, v in
                row_name_to_id_mapper_sub.items()}
            subject_info[subject_id] = subject_dict

    # Read Input CSV with subject_id column
    combined_data = list()
    n_subjects_not_found = 0
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
            if subject_id in subject_info:
                subject_info_current = subject_info[subject_id]
                # input info
                combined_info = {
                    **subject_info_current,
                    **{k: line[v] for k, v in row_name_to_id_mapper.items()}
                    }
            else:
                n_subjects_not_found += 1
                if n_subjects_not_found < 10:
                    logger.debug(
                        "subject_id {} not found in subject_csv".format(
                            subject_id))
                combined_info = {
                    k: line[v] for
                    k, v in row_name_to_id_mapper.items()}
            combined_data.append(combined_info)

    logger.info("Subjects not found in subject_csv: {}".format(
        n_subjects_not_found))

    # duplicate subject_id
    header_no_subject = [x for x in header if x != 'subject_id']
    output_header = header_subject + header_no_subject

    # Output all combined records
    with open(args['output_csv'], 'w') as f:
        csv_writer = csv.writer(f, delimiter=',')
        logger.info("Writing output to {}".format(args['output_csv']))
        csv_writer.writerow(output_header)
        tot = len(combined_data)
        for line_no, record in enumerate(combined_data):
            # get subject info data
            to_write = list()
            for x in output_header:
                try:
                    to_write.append(record[x])
                except:
                    to_write.append('')
            csv_writer.writerow(to_write)
            # print status
            if ((line_no % 10000) == 0) and (line_no > 0):
                print("Wrote {:,} records".format(line_no))
        logger.info("Wrote {} records to {}".format(
            line_no+1, args['output_csv']))
