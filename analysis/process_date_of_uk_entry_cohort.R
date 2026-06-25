###################################################
# This script creates descriptive demographic tables for individuals who only have a date of uk entry code
# (and no other migration-related codes)
#
# Author: Yamina Boukari
#   Bennett Institute for Applied Data Science
#   University of Oxford, 2026
#
###################################################

library(tidyverse)
library(here)
library(arrow)
library(skimr)
library(fs)

## Create output directory
output_dir <- here::here("output", "tables")
fs::dir_create(output_dir)

cohort_file <- "output/cohorts/full_study_cohort.arrow"
output_file <- "output/tables/demographics_date_of_uk_entry_and_no_other_migration_info_cohort.csv"

# Parse command-line argument
args <- commandArgs(trailingOnly=TRUE)
print(commandArgs(trailingOnly=TRUE))

# Import data ----
cohort <- read_feather(cohort_file) %>%
  mutate(
    across(
      where(is.ordered),
      ~ factor(as.character(.x))
    )
  )

# Summarize ----- 

vars_to_summarise <- c(
  "year_of_birth_band",
  "sex",
  "region",
  "latest_ethnicity_6_level_group",
  "imd_quintile"
)

rounding <- function(vars) {
  case_when(vars == 0 ~ 0,
            vars > 7 ~ round(vars / 5) * 5)
}

date_of_uk_entry_cohort <- cohort %>%
  filter(date_of_uk_entry, !any_migrant, !born_in_uk, !british_ethnicities)

table_freq <- date_of_uk_entry_cohort %>%
  pivot_longer(
    cols = all_of(vars_to_summarise),
    names_to = "subgroup",
    values_to = "category") %>%
  count(
    subgroup, 
    category,
    name = "n"
  ) %>%
  mutate(
    category = fct_explicit_na(category, "unknown"),
    n = rounding(n),
    percentage = round((100 * n / sum(n, na.rm = TRUE)),1)
  ) 

table_freq <- date_of_uk_entry_cohort %>%
  pivot_longer(
    cols = all_of(vars_to_summarise),
    names_to = "subgroup",
    values_to = "category"
  ) %>%
  mutate(category = fct_explicit_na(category, "unknown")) %>%
  count(subgroup, category, name = "n") %>%
  group_by(subgroup) %>%
  mutate(
    percentage = round(100 * n / sum(n), 1)
  ) %>%
  ungroup()

dir_create(path_dir(output_file))
write_csv(table_freq, path = output_file)

