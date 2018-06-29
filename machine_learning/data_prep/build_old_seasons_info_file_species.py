""" Build an info file for model training using data from seasons 1-8 """
import os
import csv
import random

# Parameters
output_file = '/home/packerc/shared/machine_learning/data/info_files/SER/species_prev.csv'
class_paths = '/home/packerc/shared/machine_learning/data/info_files/SER/'
file_names = ['S1_6.csv', 'S9_species.csv', 'S8.csv', 'S7_species.csv']
# 14292 in species train for S11
sampling_size = 9*1500

all_records = list()
for file in file_names:
    file_path = os.path.join(class_paths, file)
    with open(file_path, 'r') as f:
        csv_reader = csv.reader(f, delimiter=',')
        for line in csv_reader:
            # remove capture id
            line.pop(1)
            all_records.append(line)
# sample
final_sample = random.sample(all_records, sampling_size)

# Write to disk
with open(output_file, 'w') as f:
    csv_writer = csv.writer(f, delimiter=',')
    for line in final_sample:
        csv_writer.writerow(line)
