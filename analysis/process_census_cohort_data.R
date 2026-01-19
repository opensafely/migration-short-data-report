###################################################
# This script creates descriptive demographic tables for the census cohorts 
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

# Parse command-line argument
args <- commandArgs(trailingOnly=TRUE)

print(commandArgs(trailingOnly=TRUE))

cohort_file <- args[[1]]
#cohort_file <- "output/cohorts/census_2011_study_cohort.arrow"
output_file <- args[[2]]

# Import data ----
cohort <- read_feather(cohort_file) %>%
  mutate(
    across(
      where(is.ordered),
      ~ factor(as.character(.x))
    )
  )

  rounding <- function(vars) {
  case_when(vars == 0 ~ 0,
            vars > 7 ~ round(vars / 5) * 5)
}

# Summarize ----- 

vars_to_summarise <- c(
  "age_band",
  "sex",
  "region",
  "latest_ethnicity_6_level_group",
  "imd_quintile"
)

mig_vars <- c(
  "mig_status_2_cat")

table_freq <- cohort %>%
  pivot_longer(
    cols = all_of(vars_to_summarise),
    names_to = "subgroup",
    values_to = "category"
  ) %>%
  pivot_longer(
    cols = all_of(mig_vars),
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
    percentage = 100 * n / sum(n)
  ) %>%
  ungroup()

dir_create(path_dir(output_file))
write_csv(table_freq, path = output_file)

