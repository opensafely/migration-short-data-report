###################################################
# This script plots a histogram of all first migration codes for people eligible to be in the full cohort, without date restrictions on the 
# timing of the migration code  
#
# Author: Yamina Boukari
#   Bennett Institute for Applied Data Science
#   University of Oxford, 2026
#
###################################################

library(tidyverse)
library(lubridate)
library(here)
library(arrow)
library(skimr)
library(fs)

## Create output directory
output_dir <- here::here("output", "figures")
fs::dir_create(output_dir)

cohort_file <- "output/cohorts/full_study_cohort.arrow"

# Import data ----
cohort <- read_feather(cohort_file) %>%
  mutate(
    across(
      where(is.ordered),
      ~ factor(as.character(.x))
    )
  )

png("output/figures/histogram_migration_coding_no_restrictions.png", width = 800, height = 600)

hist(cohort$date_of_first_migration_code_no_restrictions,
     main = "Distribution of Dates",
     xlab = "Date",
     breaks = "years")

dev.off()
