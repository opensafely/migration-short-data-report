# script to describe code usage (note that how this corresponds to individuals is in the 3-annual_counts folder)
# 1) number of all migration-related codes overall and annually
# 2) number of migration-related codes split into the codelist subthemes overall and annually 
# 3) combinations of migration-related codes

# load packages

import pyarrow.feather as feather
import pandas as pd
import numpy as np

# read in data

table = feather.read_table("output/cohorts/migration_event_level_dataset/migration_related_codes.arrow")
