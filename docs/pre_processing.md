# Pre-Processing Camera-Trap Images

The following codes can be used to:

1. Process and check camera trap images
2. Inspect potential issues to resolve/waive them
3. Obtain a cleaned inventory of the processed camera trap images
4. Re-name all images


The following examples was run with the following paramters.

```
ssh lab
qsub -I -l walltime=6:00:00,nodes=1:ppn=4,mem=16gb
module load python3
cd $HOME/snapshot_safari_misc
git pull
SITE=APN
SEASON=APN_S2
```

It is recommended to create the following directories:
```
captures
cleaned
log_files
```


## Check Import/Directory Structure

The camera trap images to be imported need to be organized according to the following directory structure:

```
root_directory/
  site_directory/
    roll_directory/
      image_files
```

Definitions:
- Site: A specific camera/location.
- Roll: An SD card of a specific location (data from a camera check).

The naming has to adhere to these standards:
- site_directory: alphanumeric
- roll_directory: site name, followed by 'RX', e.g., A01_R1 (first roll of A01)
- Images: arbitrary names

```
root_directory/
  A01/
    A01_R1/
      *.JPG
```   

The check can be performed using the following script:
```
python3 -m pre_processing.check_input_structure \
--root_dir /home/packerc/shared/albums/${SITE}/${SEASON}/ \
--log_dir /home/packerc/shared/season_captures/${SITE}/log_files/
```

## Create Image Inventory

The following script generates an inventory of all camera trap images and performs some basic checks. The code is parallelized to speed up the checks -- use the following options to make the most of the parallelization:

```
ssh lab
qsub -I -l walltime=2:00:00,nodes=1:ppn=16,mem=16gb
module load python3
cd $HOME/snapshot_safari_misc
git pull
SITE=APN
SEASON=APN_S2
```

Then run the code:
```
python3 -m pre_processing.create_image_inventory \
--root_dir /home/packerc/shared/albums/${SITE}/${SEASON}/ \
--output_csv /home/packerc/shared/season_captures/${SITE}/captures/${SEASON}_inventory.csv \
--log_dir /home/packerc/shared/season_captures/${SITE}/log_files/ \
--n_processes 16
```

## Group Images into Captures

The following script groups the images into capture events.

```
python3 -m pre_processing.group_inventory_into_captures \
--inventory /home/packerc/shared/season_captures/${SITE}/captures/${SEASON}_inventory.csv \
--output_csv /home/packerc/shared/season_captures/${SITE}/captures/${SEASON}_captures.csv \
--log_dir /home/packerc/shared/season_captures/${SITE}/log_files/ \
--no_older_than_year 2017 \
--no_newer_than_year 2019
```

## Rename all images

The following script renames the images.

```
python3 -m pre_processing.rename_images \
--inventory /home/packerc/shared/season_captures/${SITE}/captures/${SEASON}_captures.csv \
--log_dir /home/packerc/shared/season_captures/${SITE}/log_files/
```

## Generate Action List

The following script generates an action list that recommends actions and allows for adding more actions.

```
python3 -m pre_processing.create_action_list \
--captures /home/packerc/shared/season_captures/${SITE}/captures/${SEASON}_captures.csv \
--action_list_csv /home/packerc/shared/season_captures/${SITE}/captures/${SEASON}_action_list.csv \
--log_dir /home/packerc/shared/season_captures/${SITE}/log_files/ \
--plot_timelines
```

### Define Actions

1. Download the file 'action_list.csv'
2. The column 'action_to_take' is pre-populated with an action that is being applied to 'action_from_image'
3. The following 'action_to_take' values are allowed ('delete', 'timechange', 'ok', 'invalid')
4. To add new actions simply create a new row in the csv. WARNING: be careful not to change the datetime columns when adding the file in Excel, the format should be (YYYY-MM-DD HH:MM:SS)
5. The following options allow for selecting images for actions:
- specify 'action_site' to perform an action on an entire site
- specify 'action_site'/'action_roll' to perform an action on an entire roll
- specify 'action_from_image' and 'action_to_image' to perform an action on a range of images
6. For each row specify: 'action_to_take' and 'action_to_take_reason'
7. For 'timechange' in 'action_to_take' specify 'datetime_current' and 'datetime_new'. This will apply the difference between these two dates to all selected images.
8. Upload the modified csv and proceed.


## Generate Actions

This code unpacks the defined actions, performs some checks and generates a list with action items. One row per action / image.

```
python3 -m pre_processing.generate_actions \
--captures /home/packerc/shared/season_captures/${SITE}/captures/${SEASON}_captures.csv \
--action_list /home/packerc/shared/season_captures/${SITE}/captures/${SEASON}_action_list.csv \
--actions_to_perform_csv /home/packerc/shared/season_captures/${SITE}/captures/${SEASON}_actions_to_perform.csv \
--log_dir /home/packerc/shared/season_captures/${SITE}/log_files/
```
This file can be checked to ensure if everything is correct.

## Apply Actions

This code applies the actions. It updates the captures file and deletes specific images if requested.

```
python3 -m pre_processing.apply_actions \
--captures /home/packerc/shared/season_captures/${SITE}/captures/${SEASON}_captures.csv \
--actions_to_perform /home/packerc/shared/season_captures/${SITE}/captures/${SEASON}_actions_to_perform.csv \
--log_dir /home/packerc/shared/season_captures/${SITE}/log_files/
```

## Genrate Captures Cleaned

This code generates a cleaned captures file with excluded deleted images and a few more columns.

```
python3 -m pre_processing.create_captures_cleaned \
--captures /home/packerc/shared/season_captures/${SITE}/captures/${SEASON}_captures.csv \
--captures_cleaned /home/packerc/shared/season_captures/${SITE}/cleaned/${SEASON}_captures_cleaned.csv \
--log_dir /home/packerc/shared/season_captures/${SITE}/log_files/
```

## Re-check cleaned captures (OPTIONAL) -- (Experimental Feature!)

The following code can be used to re-check the cleaned captures file. This should only be necessary if timechanges were applied because this may lead to new errors. If new errors are shown (printed to the console/logfile) generate a new actions list and proceed from there. If no errors are shown, the generated file can be deleted.

```
python3 -m pre_processing.group_inventory_into_captures \
--inventory /home/packerc/shared/season_captures/${SITE}/captures/${SEASON}_captures_cleaned.csv \
--output_csv /home/packerc/shared/season_captures/${SITE}/captures/${SEASON}_captures_iterated.csv \
--log_dir /home/packerc/shared/season_captures/${SITE}/log_files/ \
--no_older_than_year 2017 \
--no_newer_than_year 2019
```
