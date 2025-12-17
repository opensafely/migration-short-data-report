###################################################
# This script creates (...)
#
# Author: Yamina Boukari
#   Bennett Institute for Applied Data Science
#   University of Oxford, 2025
###################################################

library(tidyverse)
library(lubridate)

## Create output directory
output_dir <- here::here("output", "report")
fs::dir_create(output_dir)

# Import processed data ----
annual_counts <- read_csv("output/tables/annual_migrant_counts.csv")
annual_counts_2cat <- read_csv("output/tables/annual_migrant_counts_2cat.csv")
annual_counts_3cat <- read_csv("output/tables/annual_migrant_counts_3cat.csv")
annual_counts_6cat <- read_csv("output/tables/annual_migrant_counts_6cat.csv")
