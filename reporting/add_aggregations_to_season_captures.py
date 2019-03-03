""" Add Zooniverse Aggregations to Season Captures """
import csv
import logging
import os
import argparse
from datetime import datetime
from collections import OrderedDict

from logger import setup_logger, create_logfile_name
from utils import read_cleaned_season_file

# args = dict()
# args['season_captures_csv'] = '/home/packerc/shared/season_captures/GRU/cleaned/GRU_S1_cleaned.csv'
# args['aggregated_csv'] = '/home/packerc/shared/zooniverse/Exports/GRU/GRU_S1_classifications_aggregated_samples_subject_info.csv'
# args['output_csv'] = '/home/packerc/shared/zooniverse/Exports/GRU/GRU_S1_report.csv'
# args['default_season_id'] = 'GRU_S1'

if __name__ == '__main__':

    # Parse command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("--season_captures_csv", type=str, required=True)
    parser.add_argument("--aggregated_csv", type=str, required=True)
    parser.add_argument("--output_csv", type=str, required=True)
    parser.add_argument("--default_season_id", type=str, default='')
    parser.add_argument("--export_only_with_aggregations", action="store_true")

    args = vars(parser.parse_args())

    ######################################
    # Check Input
    ######################################

    if not os.path.isfile(args['season_captures_csv']):
        raise FileNotFoundError("season_captures_csv: {} not found".format(
                                args['season_captures_csv']))

    if not os.path.isfile(args['aggregated_csv']):
        raise FileNotFoundError("aggregated_csv: {} not found".format(
                                args['aggregated_csv']))

    # logging
    log_file_name = create_logfile_name('add_aggregations_to_season_captures')
    log_file_path = os.path.join(
        os.path.dirname(args['output_csv']), log_file_name)
    setup_logger(log_file_path)
    logger = logging.getLogger(__name__)

    season_data, header = read_cleaned_season_file(args['season_captures_csv'])

    # Create per Capture Data
    season_dict = OrderedDict()
    for image_record in season_data:
        capture_id = '#'.join([
            image_record[header['season']],
            image_record[header['site']],
            image_record[header['roll']],
            image_record[header['capture']],
        ])
        if capture_id not in season_dict:
            timestamp = image_record[header['timestamp']]
            # deal with different timeformats in different capture files
            try:
                time_obj = datetime.strptime(timestamp, '%Y:%m:%d %H:%M:%S')
            except ValueError:
                try:
                    time_obj = datetime.strptime(
                        timestamp,
                        '%Y-%m-%d %H:%M:%S')
                except ValueError:
                    time_obj = datetime.strptime(
                        timestamp,
                        '%Y-%m-%d %H:%M:%SZ')

            date = time_obj.strftime("%Y-%m-%d")
            time = time_obj.strftime("%H:%M:%S")
            season_dict[capture_id] = {
                'capture_id': capture_id,
                'season': image_record[header['season']],
                'site': image_record[header['site']],
                'roll': image_record[header['roll']],
                'capture': image_record[header['capture']],
                'capture_date_local': date,
                'capture_time_local': time}

    season_header = list(season_dict[capture_id].keys())

    # Import Aggregated Data
    aggregated_data = dict()
    with open(args['aggregated_csv'], "r") as ins:
        csv_reader = csv.reader(ins, delimiter=',', quotechar='"')
        header_input = next(csv_reader)
        row_name_to_id_mapper_input = {x: i for i, x in enumerate(header_input)}
        for line_no, line in enumerate(csv_reader):
            roll = line[row_name_to_id_mapper_input['roll']]
            season = line[row_name_to_id_mapper_input['season']]
            if season == '':
                season = args['default_season_id']
            site = line[row_name_to_id_mapper_input['site']]
            capture = line[row_name_to_id_mapper_input['capture']]
            capture_id = '#'.join([season, site, roll, capture])
            input_dict = {
                k: line[v] for k, v in
                row_name_to_id_mapper_input.items()}
            input_dict['capture_id'] = capture_id
            if capture_id not in aggregated_data:
                aggregated_data[capture_id] = list()
            aggregated_data[capture_id].append(input_dict)

    agg_data_header = [x for x in header_input if x not in season_header]
    header_combined = season_header + agg_data_header

    # Write Season File with Aggregations
    with open(args['output_csv'], 'w') as f:
        csv_writer = csv.writer(f, delimiter=',')
        logger.info("Writing output to {}".format(args['output_csv']))
        csv_writer.writerow(header_combined)
        n_lines_written = 0
        n_lines_with_aggregations = 0
        for line_no, (capture_id, season_data) in enumerate(season_dict.items()):
            # get subject info data
            season_info_to_write = list()
            for x in season_header:
                try:
                    season_info_to_write.append(season_data[x])
                except:
                    season_info_to_write.append('')
            # write one line for each aggregation
            if capture_id in aggregated_data:
                for agg_data_dict in aggregated_data[capture_id]:
                    to_write = list()
                    for x in agg_data_header:
                        try:
                            to_write.append(agg_data_dict[x])
                        except:
                            to_write.append('')
                    csv_writer.writerow(season_info_to_write + to_write)
                    n_lines_written += 1
                    n_lines_with_aggregations += 1
            else:
                # Write records without any aggregation information
                if not args['export_only_with_aggregations']:
                    to_write = ['' for i in range(0, len(agg_data_header))]
                    csv_writer.writerow(season_info_to_write + to_write)
                    n_lines_written += 1
            # print status
            if ((line_no % 10000) == 0) and (line_no > 0):
                print("Processed {:,} captures".format(line_no))
        logger.info("Wrote {} records to {}".format(
            n_lines_written, args['output_csv']))
        logger.info("Wrote {} records with aggregations to {}".format(
            n_lines_with_aggregations, args['output_csv']))

    # change permmissions to read/write for group
    os.chmod(args['output_csv'], 0o660)
