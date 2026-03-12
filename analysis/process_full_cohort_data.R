###################################################
# This script creates descriptive demographic tables for the overall full cohort 
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

# Parse command-line argument
args <- commandArgs(trailingOnly=TRUE)
print(commandArgs(trailingOnly=TRUE))

output_file <- args[[1]]
mig_vars <- args[[2]]

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

table_freq_overall <- cohort %>%
  pivot_longer(
    cols = all_of(mig_vars),
    #cols = all_of("mig_status_3_cat"),
    names_to = "migration_scheme",
    values_to = "migration_status"
  ) %>%
  # make missing explicit if needed
  mutate(
    migration_status = fct_explicit_na(migration_status, "unknown")
  ) %>%
  count(
    migration_scheme,
    migration_status,
    name = "n"
  ) %>%
  group_by(migration_scheme) %>%
  mutate(
    subgroup = "All",
    category = "All",
    n = rounding(n),
    percentage = round((100 * n / sum(n, na.rm = TRUE)),1)
  ) %>%
  ungroup() 

table_freq <- cohort %>%
  pivot_longer(
    cols = all_of(vars_to_summarise),
    names_to = "subgroup",
    values_to = "category"
  ) %>%
  pivot_longer(
    cols = all_of(mig_vars),
    #cols = all_of("mig_status_3_cat"),
    names_to = "migration_scheme",
    values_to = "migration_status"
  ) %>%
  # make missing explicit if needed
  mutate(
    category = fct_explicit_na(category, "unknown"),
    migration_status = fct_explicit_na(migration_status, "unknown")
  ) %>%
  count(
    migration_scheme,
    migration_status,
    subgroup,
    category,
    name = "n"
  ) %>%
  group_by(migration_scheme, migration_status, subgroup) %>%
  mutate(
    n = rounding(n),
    percentage = round((100 * n / sum(n, na.rm = TRUE)),1)
  ) %>%
  ungroup() 

table_freq <- bind_rows(table_freq_overall, table_freq)
table_freq <- table_freq %>%
  relocate(n, .before= percentage)

dir_create(path_dir(output_file))
write_csv(table_freq, path = output_file)

