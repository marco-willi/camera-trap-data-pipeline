# snapshot_safari_misc
This repository contains code for the following tasks:

1. [Pre-Processing Camera-Trap Images](docs/pre_processing.md) - in development
2. [Upload Data to Zooniverse](docs/zooniverse_uploads.md) - allows for adding machine learning scores
3. [Download & Extract Data from Zooniverse](docs/zooniverse_exports.md)
4. [Aggregate Data from Zooniverse](docs/zooniverse_aggregations.md)
5. [Merge Data into Reports](docs/reporting.md) - in development

Most codes produce log-files containing important information about how the data was processed.

## Overview

A high-level overview of how the scripts are connected can be found here:
[Process Overview](docs/data_processing_overview.pdf)

## Configuration

Parameters that define the behavior of some codes are defined here: [config/cfg.yaml](config/cfg.yaml)

These need to be adjusted, for example:
1. if a new question answer needs to be mapped to 'empty', e.g., 'no animal is here'
2. if a new question needs to be renamed, e.g., 'howmanyanimalswithbighornsdoyousee' to 'big_horns_count'
3. if different formats / namings are required, e.g., 'answer__' instead of 'question__'

## Executing the Scripts

The recommended way is to use parameters and then run the scripts as shown here: [Scripts](scripts.sh)

Alternatively, copy & paste the commands to a text editor, adjust the parameters, and copy & paste them to the command line.

## Pre-Requisites

### Prepare Zooniverse-Access (one-time only)

For code that accesses Zooniverse via Panoptes (e.g. requires a password),
a file with Zooniverse credentials should be stored. Default location for that file is:  "~/keys/passwords.ini". It should have the following content:

```
[zooniverse]
username: my_username
password: my_password
```

Set permissions of that file by using this command (remove any access rights other than yours):
```
chmod 600 ~/keys/passwords.ini
```

### Get the codes from GitHub

To execute the following codes we need the most recent version of the GitHub code. We will clone the code into the our home directory. This avoids any conflicts with permissions and will create a directory 'snapshot_safari_misc' in your home directory.

```
cd
git clone https://github.com/marco-willi/snapshot_safari_misc.git
```

If that code / directory already exists you can update it using following command:

```
cd ~/snapshot_safari_misc
git pull
```

Should there be any conflicts / issues, just delete your code and clone again. Any changes you made to the code are lost after this.
```
rm -r -f ~/snapshot_safari_misc
cd
git clone https://github.com/marco-willi/snapshot_safari_misc.git
```


### Prepare Python

Before executing (most of) the code, you need to execute the follwing:
```
ssh lab
module load python3
pip install --upgrade --user panoptes-client
pip install --upgrade --user pillow
cd ~/snapshot_safari_misc
```
