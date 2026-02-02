###################################################
# This script carries out checks on all date variables 
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
output_dir <- here::here("output", "tables")
fs::dir_create(output_dir)

# Checks:
# - Who has a first migration code date that is before their date of birth
# - Has a first migration code date that is before first practice reg
# - Has a first migration code date that is after date of death

cohort_file <- "output/cohorts/full_study_cohort.arrow"
output_file <- "output/tables/date_variable_checks.csv"

# Import data ----
cohort <- read_feather(cohort_file) %>%
  mutate(
    across(
      where(is.ordered),
      ~ factor(as.character(.x))
    )
  )

check_dates <- cohort %>%
  mutate(# These should all be 0 
    rtt_end_before_start = ifelse(rtt_end_date < rtt_start_date, 1, 0),
    rtt_end_after_dod = ifelse(!is.na(dod) & (rtt_end_date > dod), 1, 0),
    dereg_before_rtt_start = ifelse(!is.na(reg_end_date) & (reg_end_date < rtt_start_date), 1, 0),
    rtt_end_missing = ifelse(is.na(rtt_end_date), 1, 0),
    rtt_start_missing = ifelse(is.na(rtt_start_date), 1, 0),
    end_before_start = ifelse(end_date < rtt_start_date, 1, 0)
  ) %>%
  summarise(rtt_end_before_start = sum(rtt_end_before_start),
            rtt_end_after_dod = sum(rtt_end_after_dod),
            dereg_before_rtt_start = sum(dereg_before_rtt_start),
            rtt_end_missing = sum(rtt_end_missing),
            rtt_start_missing = sum(rtt_start_missing),
            end_before_start = sum(end_before_start),
            # Check max wait time for developing code
            max_wait_time = max(wait_time),
  )
