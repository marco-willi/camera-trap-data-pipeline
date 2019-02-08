# snapshot_safari_misc
This repository contains code for the following tasks:

1. [Upload Data to Zooniverse](docs/zooniverse_uploads.md)
2. [Download & Extract Data from Zooniverse](docs/zooniverse_exports.md)
3. [Aggregate Data from Zooniverse](docs/zooniverse_aggregations.md)
4. [Merge Data into Reports](docs/reporting.md) - in development

## Overview

A high-level overview of how the scripts are connected can be found here:
[Process Overview](docs/data_processing_overview.pdf)

Note that not all processes are implemented in this repository and some of it represents a roadmap.

## Example Scripts

Here a compilation of many sample scripts [Scripts](scripts.sh)

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

### Execute Codes

The easiest way to exectue the following codes is to copy & paste them to a text editor, change the parameters (e.g. paths) and then copy & paste that to the command line to execute them.
