# Pre-Processing Camera-Trap Images

The following codes can be used to:

1. Create Image Inventory
2. Extract Exif data
3. Perform basic checks
4. Group images into captures
5. Inspect potential issues to resolve/waive them
6. Obtain a cleaned inventory of the processed camera trap images
7. Re-name all images


The following examples were run with the following settings:

```
ssh lab
qsub -I -l walltime=6:00:00,nodes=1:ppn=4,mem=16gb
module load python3
cd $HOME/camera-trap-data-pipeline
git pull
SITE=APN
SEASON=APN_S2
```

It is recommended to create the following directories:
```
season_captures/${SITE}/inventory
season_captures/${SITE}/captures
season_captures/${SITE}/cleaned
season_captures/${SITE}/log_files
```


## Check Import (directory) Structure

The camera trap images to be imported need to be organized according to the following directory structure:

```
root_directory/
  site_directory/
    roll_directory/
      image_files
```

Definitions:
- Site: A specific camera/location.
- Roll: An SD card of a specific site (data from a camera check).

The naming has to adhere to these standards:
- site_directory: alphanumeric
- roll_directory: site name + _ + 'RX' where 'X' is a numeric. Example: A01_R1 (first roll of A01).
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

The script will print/log messages if something is invalid but not alter anything.

## Create Image Inventory

The following script generates an inventory of all camera trap images.

```
python3 -m pre_processing.create_image_inventory \
--root_dir /home/packerc/shared/albums/${SITE}/${SEASON}/ \
--output_csv /home/packerc/shared/season_captures/${SITE}/inventory/${SEASON}_inventory_basic.csv \
--log_dir /home/packerc/shared/season_captures/${SITE}/log_files/
```


## Perform Basic Checks

The following script performs some basic checks. The code is parallelized to speed up the checks -- use the following options to make the most of the parallelization (it still takes roughly 1 hour per 60k images).

```
ssh lab
qsub -I -l walltime=2:00:00,nodes=1:ppn=16,mem=16gb
module load python3
cd $HOME/camera-trap-data-pipeline
git pull
SITE=APN
SEASON=APN_S2
```

Then run the code:
```
python3 -m pre_processing.basic_inventory_checks \
--inventory /home/packerc/shared/season_captures/${SITE}/inventory/${SEASON}_inventory_basic.csv \
--output_csv /home/packerc/shared/season_captures/${SITE}/inventory/${SEASON}_inventory.csv \
--log_dir /home/packerc/shared/season_captures/${SITE}/log_files/ \
--n_processes 16
```

## Extract EXIF data

The following script extracts EXIF data from all images.

```
python3 -m pre_processing.extract_exif_data \
--inventory /home/packerc/shared/season_captures/${SITE}/inventory/${SEASON}_inventory.csv \
--update_inventory \
--output_csv /home/packerc/shared/season_captures/${SITE}/inventory/${SEASON}_exif_data.csv \
--exiftool_path /home/packerc/shared/programs/Image-ExifTool-11.31/exiftool \
--log_dir /home/packerc/shared/season_captures/${SITE}/log_files/
```


## Group Images into Captures

The following script groups the images into capture events.

```
python3 -m pre_processing.group_inventory_into_captures \
--inventory /home/packerc/shared/season_captures/${SITE}/inventory/${SEASON}_inventory.csv \
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

The option '--plot_timelines' creates a pdf in the '--action_list_csv' directory with timelines for each roll showing the number of photos per day. This can be used to identify potential issues.

### Define Actions

1. Download the file 'action_list.csv'
2. The file is pre-populated with suggested actions that are being applied to the 'action_from_image'.
3. The following 'action_to_take' values are allowed:

action_to_take | meaning
------------ | -------------
delete | the selected images will be deleted
timechange | the time of the selected images will be changed (see below)
ok | do nothing
invalid | do nothing, but keep invalid flag

4. To add new actions simply create a new row in the csv.

WARNING: be careful in using the correct datetime format for the columns 'datetime_current' and 'datetime_new' (YYYY-MM-DD HH:MM:SS) when specifying timechanges. Opening the file in Excel may change this format.

5. The following options allow for selecting images for actions:

column(s) to specify | meaning
------------ | -------------
action_site | perform an action on an entire site
action_site / action_roll | perform an action on an entire roll
action_from_image / action_to_image | perform an action on a range of images (or one if identical)

Examples:

action_site	| action_roll | action_from_image |	action_to_image	| action_to_take |action_to_take_reason | datetime_current |	datetime_new
:---|:---|:--- | :---| :---| :---|:---|:---
 A01| | |		|delete	|camera_produced_unrecognizable_images	||
 A01| 2| |		|timechange	|camera clock off by minus one day	| 2000-01-01 00:00:00| 2000-01-02 00:00:00		
 | | |ENO_S1__B02_R1_IMAG1012.JPG	| ENO_S1__B02_R1_IMAG1012.JPG	|delete	|all_white		||
 | | |ENO_S1__B02_R1_IMAG0054.JPG	| ENO_S1__B02_R1_IMAG0054.JPG	|delete	|all_black||
 | | |ENO_S1__B02_R1_IMAG0990.JPG	|ENO_S1__B02_R1_IMAG0999.JPG	|delete	|human	||


6. For each row specify: 'action_to_take' and 'action_to_take_reason'
7. For 'timechange' in 'action_to_take' specify 'datetime_current' and 'datetime_new'. This will apply the difference between these two dates to all selected images.
8. All rows with 'action_to_take' equal 'inspect' must be resolved and replaced with values as specified above.
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

## Generate Updated Captures

This code generates an updated captures file after applying actions. Deleted images are excluded and a few more columns added.

```
python3 -m pre_processing.update_captures \
--captures /home/packerc/shared/season_captures/${SITE}/captures/${SEASON}_captures.csv \
--captures_updated /home/packerc/shared/season_captures/${SITE}/captures/${SEASON}_captures_updated.csv \
--log_dir /home/packerc/shared/season_captures/${SITE}/log_files/
```

## Finalize (create cleaned captures) or Iterate (go back to creating action list)

If the previous code showed no further issues in the printed output, the generated file is the finalized cleaned captures file and can be moved like this:
```
cp /home/packerc/shared/season_captures/${SITE}/captures/${SEASON}_captures_updated.csv /home/packerc/shared/season_captures/${SITE}/cleaned/${SEASON}_captures_cleaned.csv
```

If there are further issues, we generate a new action list and start over with:

```
python3 -m pre_processing.create_action_list \
--captures /home/packerc/shared/season_captures/${SITE}/captures/${SEASON}_captures_updated.csv \
--action_list_csv /home/packerc/shared/season_captures/${SITE}/captures/${SEASON}_action_list2.csv \
--log_dir /home/packerc/shared/season_captures/${SITE}/log_files/
```

This code can be run in any case to check if further actions need to be taken if the output of the previous code (update_captures) was not clear.
