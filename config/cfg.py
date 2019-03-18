""" Read Config File """
import yaml
import os

working_dir = os.path.abspath(os.path.dirname(__file__))
cfg_path = os.path.join(working_dir, "../config/cfg.yaml")
cfg = yaml.load(open(cfg_path, 'r'), Loader=yaml.FullLoader)

# Read Mappings (if available)
try:
    ml_mappings_path = os.path.join(working_dir, "../config/ml_mappings.yaml")
    ml_mappings = yaml.load(open(ml_mappings_path, 'r'), , Loader=yaml.FullLoader)
except:
    ml_mappings = None
