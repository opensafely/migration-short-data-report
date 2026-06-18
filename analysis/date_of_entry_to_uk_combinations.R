###################################################
# This script describes the number of individuals with a date of uk entry code
# and other migration-related codes 
#
# Author: Yamina Boukari
#   Bennett Institute for Applied Data Science
#   University of Oxford, 2026
#
###################################################

library(tidyverse)

cohort_file <- "output/cohorts/full_study_cohort.arrow"
output_file <- "output/tables/date_of_uk_entry_combinations.csv"

# Import data ----
cohort <- read_feather(cohort_file) %>%
  mutate(
    across(
      where(is.ordered),
      ~ factor(as.character(.x))
    )
  )

summary_combinations <- cohort %>%
  count(date_of_uk_entry,
        any_migrant,
        born_in_uk,
        british_ethnicities)

dir_create(path_dir(output_file))
write_csv(summary_combinations, path = output_file)
