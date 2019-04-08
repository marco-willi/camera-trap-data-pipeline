""" Read Config File """
import yaml
import os

working_dir = os.path.abspath(os.path.dirname(__file__))

# load cfg.yaml if available, otherwise, load cfg_default.yaml
try:
    cfg_path = os.path.join(working_dir, "../config/cfg.yaml")
    cfg = yaml.load(open(cfg_path, 'r'))
except:
    # load default config
    cfg_path = os.path.join(working_dir, "../config/cfg_default.yaml")
    cfg = yaml.load(open(cfg_path, 'r'))

# separately, load default cfg
try:
    cfg_path = os.path.join(working_dir, "../config/cfg_default.yaml")
    cfg_default = yaml.load(open(cfg_path, 'r'))
except:
    cfg_default = None

# Read Mappings (if available)
try:
    ml_mappings_path = os.path.join(working_dir, "../config/ml_mappings.yaml")
    ml_mappings = yaml.load(open(ml_mappings_path, 'r'))
except:
    ml_mappings = None
