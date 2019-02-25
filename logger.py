""" Logging """
import logging
import sys
import getpass

from utils import set_file_permission


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
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s - %(funcName)s - %(levelname)s:' +
                               '%(message)s',
                        handlers=handlers)
    logging.info("{} is running the script".format(getpass.getuser()))
    if log_file is not None:
        set_file_permission(log_file)
