""" Read Config File """
import yaml
import os

working_dir = os.path.abspath(os.path.dirname(__file__))
cfg_path = os.path.join(working_dir, "../config/cfg.yaml")
cfg = yaml.load(open(cfg_path, 'r'))
