###################################################
# This script describes the age of the census cohorts 
#
# Author: Yamina Boukari
#   Bennett Institute for Applied Data Science
#   University of Oxford, 2026
#
###################################################

library(tidyverse)
library(arrow)
library(fs)

# Parse command-line argument
args <- commandArgs(trailingOnly=TRUE)

print(commandArgs(trailingOnly=TRUE))

cohort_file <- args[[1]]
#cohort_file <- "output/cohorts/census_2021_study_cohort.arrow"
output_file <- args[[2]]
mig_vars <- args[[3]]

cohort <- read_feather(cohort_file) %>%
  mutate(
    across(
      where(is.ordered),
      ~ factor(as.character(.x))
    )
  )

table_median_iqr <- cohort %>%
  pivot_longer(
    #cols = all_of(mig_vars),
    cols = all_of("mig_status_3_cat"),
    names_to = "migration_scheme",
    values_to = "migration_status"
  ) %>%
  # make missing explicit if needed
  mutate(
    migration_status = fct_explicit_na(migration_status, "unknown")
  ) %>%
  group_by(migration_status) %>%
  summarise(
    median_age = median(age_on_census_date),
    q25_age = quantile(age_on_census_date, 0.25, na.rm = TRUE),
    q75_age = quantile(age_on_census_date, 0.75, na.rm = TRUE)) %>%
  ungroup() 

dir_create(path_dir(output_file))
write_csv(table_median_iqr, path = output_file)

