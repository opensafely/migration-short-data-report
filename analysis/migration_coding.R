###################################################
# This script describes migration coding 
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
output_file <- "output/tables/migration_coding_summary.csv"

# Import data ----
cohort <- read_feather(cohort_file) %>%
  mutate(
    across(
      where(is.ordered),
      ~ factor(as.character(.x))
    )
  )

vars_to_summarise <- c(
  "year_of_birth_band",
  "sex",
  "region",
  "latest_ethnicity_6_level_group",
  "imd_quintile"
)

mig_vars <- c(
  "mig_status_2_cat",
  "mig_status_3_cat",
  "mig_status_6_cat")

migration_coding_summary <- cohort %>%
  pivot_longer(
    cols = all_of(mig_vars),
    names_to = "migration_scheme",
    values_to = "migration_status"
  ) %>%
  group_by(migration_scheme, migration_status) %>%
  summarise(
    n = n(),
    total_migration_codes = sum(number_of_migration_codes),
    median_migration_codes = median(number_of_migration_codes, na.rm = TRUE),
    q25_migration_codes = quantile(number_of_migration_codes, 0.25, na.rm = TRUE),
    q75_migration_codes = quantile(number_of_migration_codes, 0.75, na.rm = TRUE),
    median_time_to_1st_migration_code_days = median(time_to_first_migration_code_days, na.rm = TRUE),
    q25_time_to_first_migration_code_days = quantile(time_to_first_migration_code_days, 0.25, na.rm = TRUE),
    q75_time_to_first_migration_code_days = quantile(time_to_first_migration_code_days, 0.75, na.rm = TRUE),
    median_time_to_1st_migration_code_months = median(time_to_first_migration_code_months, na.rm = TRUE),
    q25_time_to_first_migration_code_months = quantile(time_to_first_migration_code_months, 0.25, na.rm = TRUE),
    q75_time_to_first_migration_code_months = quantile(time_to_first_migration_code_months, 0.75, na.rm = TRUE),
    .groups = "drop"
  ) 

dir_create(path_dir(output_file))
write_csv(migration_coding_summary, path = output_file)

