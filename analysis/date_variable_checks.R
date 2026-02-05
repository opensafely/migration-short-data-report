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
  group_by(any_migrant, has_date_of_uk_entry_at_any_time) %>%
  mutate(
    mig_code_before_birth =
      as.integer(date_of_first_migration_code < date_of_birth),
    mig_code_after_death =
      as.integer(date_of_first_migration_code > date_of_death),
    mig_code_before_first_pract_reg =
      as.integer(date_of_first_migration_code < date_of_first_practice_registration),
    uk_entry_code_before_birth =
      as.integer(date_of_earliest_date_of_uk_entry_code < date_of_birth),
    uk_entry_code_after_death =
      as.integer(date_of_earliest_date_of_uk_entry_code > date_of_death),
    uk_entry_code_before_first_pract_reg =
      as.integer(date_of_earliest_date_of_uk_entry_code < date_of_first_practice_registration),
    uk_entry_code_on_date_of_first_pract_reg =
      as.integer(date_of_earliest_date_of_uk_entry_code ==
                   date_of_first_practice_registration),
    uk_entry_code_after_first_pract_reg =
      as.integer(date_of_earliest_date_of_uk_entry_code >
                   date_of_first_practice_registration),
    mig_code_after_date_of_uk_entry_code =
      as.integer(date_of_first_migration_code >
                   date_of_earliest_date_of_uk_entry_code),
    mig_code_before_date_of_uk_entry_code =
      as.integer(date_of_first_migration_code <
                   date_of_earliest_date_of_uk_entry_code),
    mig_code_on_date_of_uk_entry_code =
      as.integer(date_of_first_migration_code ==
                   date_of_earliest_date_of_uk_entry_code),
    date_of_birth_after_date_of_death =
      as.integer(date_of_birth > date_of_death),
    date_of_first_prac_reg_before_birth =
      as.integer(date_of_first_practice_registration < date_of_birth),
    date_of_first_prac_reg_after_death =
      as.integer(date_of_first_practice_registration > date_of_death)
  ) %>%
  summarise(
    group_size = n(),
    mig_code_before_birth = sum(mig_code_before_birth, na.rm = TRUE),
    mig_code_after_death = sum(mig_code_after_death, na.rm = TRUE),
    mig_code_before_first_pract_reg = sum(mig_code_before_first_pract_reg, na.rm = TRUE),
    uk_entry_code_before_birth = sum(uk_entry_code_before_birth, na.rm = TRUE),
    uk_entry_code_after_death = sum(uk_entry_code_after_death, na.rm = TRUE),
    uk_entry_code_before_first_pract_reg = sum(uk_entry_code_before_first_pract_reg, na.rm = TRUE),
    uk_entry_code_on_date_of_first_pract_reg = sum(uk_entry_code_on_date_of_first_pract_reg, na.rm = TRUE),
    uk_entry_code_after_first_pract_reg = sum(uk_entry_code_after_first_pract_reg, na.rm = TRUE),
    mig_code_after_date_of_uk_entry_code = sum(mig_code_after_date_of_uk_entry_code, na.rm = TRUE),
    mig_code_before_date_of_uk_entry_code = sum(mig_code_before_date_of_uk_entry_code, na.rm = TRUE),
    mig_code_on_date_of_uk_entry_code = sum(mig_code_on_date_of_uk_entry_code, na.rm = TRUE),
    date_of_birth_after_date_of_death = sum(date_of_birth_after_date_of_death, na.rm = TRUE),
    date_of_first_prac_reg_before_birth = sum(date_of_first_prac_reg_before_birth, na.rm = TRUE),
    date_of_first_prac_reg_after_death = sum(date_of_first_prac_reg_after_death, na.rm = TRUE)
  )

dir_create(path_dir(output_file))
write_csv(check_dates, path = output_file)
