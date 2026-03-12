###################################################
# This script describes the date of entry to the UK code 
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
output_file <- "output/tables/date_of_uk_entry_description.csv"

# Import data ----
cohort <- read_feather(cohort_file) %>%
  mutate(
    across(
      where(is.ordered),
      ~ factor(as.character(.x))
    )
  )

#   rounding <- function(vars) {
#   case_when(vars == 0 ~ 0,
#             vars > 7 ~ round(vars / 5) * 5)
# }

# Number and median (IQR) of date of UK entry codes per individual 

summary_uk_entry_codes <- cohort %>%
  filter(has_date_of_uk_entry == "TRUE") %>%
  summarise(total_patients = n(),
            total_date_of_uk_entry_codes = sum(number_of_date_of_uk_entry_codes), # unsure if I need rounding here
            median_date_of_uk_entry_codes = median(number_of_date_of_uk_entry_codes, na.rm = TRUE),
            q25 = quantile(number_of_date_of_uk_entry_codes, 0.25, na.rm = TRUE),
            q75 = quantile(number_of_date_of_uk_entry_codes, 0.75, na.rm = TRUE),
            .groups = "drop")

# Timing of date of UK entry code 

timing_of_date_of_uk_entry_codes <- cohort %>%
  count(temporality_of_date_of_uk_entry_code)%>% 
  #mutate(n = rounding(n)) %>%
  pivot_wider(
    names_from = temporality_of_date_of_uk_entry_code,
    values_from = n,
    values_fill = 0
  )

summary_uk_entry_codes_sum_median_iqr_cat <- bind_cols(summary_uk_entry_codes, timing_of_date_of_uk_entry_codes)

dir_create(path_dir(output_file))
write_csv(summary_uk_entry_codes_sum_median_iqr_cat, path = output_file)

