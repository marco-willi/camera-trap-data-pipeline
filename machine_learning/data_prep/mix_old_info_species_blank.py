""" Build an info file for model training using data from seasons 1-8
    50% empty and 50% species images
"""
import csv
import random

if __name__ == '__main__':

    # Parameters
    output_file = '/home/packerc/shared/machine_learning/data/info_files/SER/blanks_species_prev.csv'
    blank_file = '/home/packerc/shared/machine_learning/data/info_files/SER/blanks_prev.csv'
    species_file = '/home/packerc/shared/machine_learning/data/info_files/SER/species_prev.csv'
    files = [blank_file, species_file]

    # 35'000 empty in S11 training set
    sampling_size = 17500

    all_records = list()
    for file_path in files:
        is_empty = 'blank' in file_path
        class_records = list()
        with open(file_path, 'r') as f:
            csv_reader = csv.reader(f, delimiter=',')
            for line in csv_reader:
                # remove capture id
                path = line[0]
                if is_empty:
                    class_flag = 0
                else:
                    class_flag = 1
                class_records.append([path, class_flag])
        class_sample = random.sample(class_records, sampling_size)
        all_records.append(class_sample)

    # randomly permuate
    random.shuffle(all_records)

    # Write to disk
    with open(output_file, 'w') as f:
        csv_writer = csv.writer(f, delimiter=',')
        for line in all_records:
            csv_writer.writerow(line)
