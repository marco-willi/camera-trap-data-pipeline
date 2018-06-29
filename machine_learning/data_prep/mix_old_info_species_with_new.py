""" Concatenate Empty Prev data with new Data
"""
import random

if __name__ == '__main__':

    # Parameters
    output_file = '/home/packerc/shared/machine_learning/data/info_files/SER/SER_S11/SER_S11_old_species_prev_train.csv'
    prev_file = '/home/packerc/shared/machine_learning/data/info_files/SER/species_prev.csv'
    current_file = '/home/packerc/shared/machine_learning/data/info_files/SER/SER_S11/SER_S11_old_species_train.csv'
    files = [prev_file, current_file]

    all_records = list()
    for file_path in files:
        with open(file_path, 'r') as f:
            for line in f:
                all_records.append(line)

    # randomly permuate
    random.shuffle(all_records)

    # Write to disk
    with open(output_file, 'w') as f:
        for r in all_records:
            f.write(r)
