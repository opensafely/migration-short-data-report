###################################################
# This script summarises the number of people by 3-cat migration status who have a migration code recorded at any time (not restricted to during their lifetime)
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
output_file <- "output/tables/summary_migration_coding_without_restrictions_by_mig_status.csv"

cohort_file <- "output/cohorts/full_study_cohort.arrow"

# Import data ----
cohort <- read_feather(cohort_file) %>%
  mutate(
    across(
      where(is.ordered),
      ~ factor(as.character(.x))
    )
  )

summary <- cohort %>%
  group_by(mig_status_3_cat_withdoe, has_first_migration_code_no_restrictions) %>%
  count()

overall_n <- cohort %>%
  group_by(mig_status_3_cat_withdoe) %>%
  count() %>%
  rename(denominator = n)

summary_full <- summary %>%
  left_join(overall_n, by = "mig_status_3_cat_withdoe") %>%
  mutate(percent = n/denominator*100)

dir_create(path_dir(output_file))
write_csv(summary_full, path = output_file)
