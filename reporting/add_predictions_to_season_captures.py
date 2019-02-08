""" Add Machine Predictions to Season Captures """
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
# args['predictions_csv'] = '/home/packerc/shared/zooniverse/Manifests/GRU/GRU_S1_machine_learning.csv'
# args['output_csv'] = '/home/packerc/shared/zooniverse/Exports/GRU/GRU_S1_report2.csv'
# args['export_only_with_predictions'] = False

if __name__ == '__main__':

    # Parse command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("--season_captures_csv", type=str, required=True)
    parser.add_argument("--predictions_csv", type=str, required=True)
    parser.add_argument("--output_csv", type=str, required=True)
    parser.add_argument("--export_only_with_predictions", action="store_true")

    args = vars(parser.parse_args())

    ######################################
    # Check Input
    ######################################

    if not os.path.isfile(args['season_captures_csv']):
        raise FileNotFoundError("season_captures_csv: {} not found".format(
                                args['season_captures_csv']))

    if not os.path.isfile(args['predictions_csv']):
        raise FileNotFoundError("predictions_csv: {} not found".format(
                                args['predictions_csv']))

    # logging
    log_file_name = create_logfile_name('add_predictions_to_season_captures')
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
            time_obj = datetime.strptime(timestamp, '%Y:%m:%d %H:%M:%S')
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

    # Import Prediction Data
    prediction_data = dict()
    with open(args['predictions_csv'], "r") as ins:
        csv_reader = csv.reader(ins, delimiter=',', quotechar='"')
        header_input = next(csv_reader)
        row_name_to_id_mapper_input = {x: i for i, x in enumerate(header_input)}
        for line_no, line in enumerate(csv_reader):
            capture_id = line[row_name_to_id_mapper_input['capture_id']]
            input_dict = {
                k: line[v] for k, v in
                row_name_to_id_mapper_input.items() if k != 'capture_id'}
            prediction_data[capture_id] = input_dict

    pred_data_header = [x for x in header_input if x not in season_header]
    header_combined = season_header + pred_data_header

    # Write Season File with Aggregations
    with open(args['output_csv'], 'w') as f:
        csv_writer = csv.writer(f, delimiter=',')
        logger.info("Writing output to {}".format(args['output_csv']))
        csv_writer.writerow(header_combined)
        n_lines_written = 0
        for line_no, (capture_id, season_data) in enumerate(season_dict.items()):
            # get subject info data
            to_write = list()
            for x in season_header:
                try:
                    to_write.append(season_data[x])
                except:
                    to_write.append('')
            try:
                pred_data_current = prediction_data[capture_id]
            except:
                if args['export_only_with_predictions']:
                    continue
                pred_data_current = {}
            for x in pred_data_header:
                try:
                    to_write.append(pred_data_current[x])
                except:
                    to_write.append('')
            csv_writer.writerow(to_write)
            n_lines_written += 1
            # print status
            if ((line_no % 10000) == 0) and (line_no > 0):
                print("Wrote {:,} captures".format(line_no))
        logger.info("Wrote {} records to {}".format(
            n_lines_written+1, args['output_csv']))
