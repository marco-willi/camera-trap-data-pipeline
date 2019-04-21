""" Logging """
import logging
import sys
import os
import getpass

from utils.utils import set_file_permission


def create_logfile_name(_id):
    """ Create a logfile name based on an identifier """
    return '{}.log'.format(_id)


def setup_logger(log_file=None):
    # log to file and console
    handlers = list()
    if log_file is not None:
        file_handler = logging.FileHandler(filename=log_file, mode='a')
        handlers.append(file_handler)
    stdout_handler = logging.StreamHandler(sys.stdout)
    handlers.append(stdout_handler)
    # logger configuration
    logging.basicConfig(level=os.environ.get("LOGLEVEL", "INFO"),
                        format='%(asctime)s - %(funcName)s - %(levelname)s:' +
                               '%(message)s',
                        handlers=handlers)
    logging.info("{} is running the script".format(getpass.getuser()))
    if log_file is not None:
        set_file_permission(log_file)


def create_log_file(log_dir, log_file_name):
    """ Create Log File Path """
    if not os.path.isdir(log_dir):
        raise FileNotFoundError(
            "log_dir {} does not exist -- must be a directory".format(
                log_dir))
    log_file_name = create_logfile_name(log_file_name)
    log_file_path = os.path.join(log_dir, log_file_name)
    return log_file_path


def set_logging(log_dir=None, log_filename=None):
    """ Small wrapper to setup logging """
    if log_dir is not None:
        log_file_path = create_log_file(log_dir, log_filename)
        setup_logger(log_file_path)
    else:
        setup_logger()
