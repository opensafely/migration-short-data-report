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
  "mig_status_6_cat",
  "mig_status_2_cat_withdoe",
  "mig_status_3_cat_withdoe",
  "mig_status_6_cat_withdoe")

rounding <- function(vars) {
  case_when(vars == 0 ~ 0,
            vars > 7 ~ round(vars / 5) * 5)
}

migration_coding_summary <- cohort %>%
  pivot_longer(
    cols = all_of(mig_vars),
    names_to = "migration_scheme",
    values_to = "migration_status"
  ) %>%
  group_by(migration_scheme, migration_status) %>%
  summarise(
    n = rounding(n()),
    # excluding date of uk entry code
    total_migration_codes = rounding(sum(number_of_migration_codes)),
    median_migration_codes = median(number_of_migration_codes, na.rm = TRUE),
    q25_migration_codes = quantile(number_of_migration_codes, 0.25, na.rm = TRUE),
    q75_migration_codes = quantile(number_of_migration_codes, 0.75, na.rm = TRUE),
    # including date of uk entry code
    total_migration_codes_withdoe = rounding(sum(number_of_migration_codes_withdoe)),
    median_migration_codes_withdoe = median(number_of_migration_codes_withdoe, na.rm = TRUE),
    q25_migration_codes_withdoe = quantile(number_of_migration_codes_withdoe, 0.25, na.rm = TRUE),
    q75_migration_codes_withdoe = quantile(number_of_migration_codes_withdoe, 0.75, na.rm = TRUE),
    # excluding date of uk entry code
    median_time_from_1st_pracreg_first_migration_code_days = median(time_from_1st_pracreg_first_migration_code_days, na.rm = TRUE),
    q25_time_from_1st_pracreg_first_migration_code_days = quantile(time_from_1st_pracreg_first_migration_code_days, 0.25, na.rm = TRUE),
    q75_time_from_1st_pracreg_first_migration_code_days = quantile(time_from_1st_pracreg_first_migration_code_days, 0.75, na.rm = TRUE),
    median_time_from_1st_pracreg_first_migration_code_months = median(time_from_1st_pracreg_first_migration_code_months , na.rm = TRUE),
    q25_time_from_1st_pracreg_first_migration_code_months = quantile(time_from_1st_pracreg_first_migration_code_months , 0.25, na.rm = TRUE),
    q75_time_from_1st_pracreg_first_migration_code_months = quantile(time_from_1st_pracreg_first_migration_code_months , 0.75, na.rm = TRUE),
    median_time_from_birth_first_migration_code_days = median(time_from_birth_first_migration_code_days, na.rm = TRUE),
    q25_time_from_birth_first_migration_code_days = quantile(time_from_birth_first_migration_code_days, 0.25, na.rm = TRUE),
    q75_time_from_birth_first_migration_code_days = quantile(time_from_birth_first_migration_code_days, 0.75, na.rm = TRUE),
    median_time_from_birth_first_migration_code_months = median(time_from_birth_first_migration_code_months, na.rm = TRUE),
    q25_time_from_birth_first_migration_code_months = quantile(time_from_birth_first_migration_code_months, 0.25, na.rm = TRUE),
    q75_time_from_birth_first_migration_code_months = quantile(time_from_birth_first_migration_code_months, 0.75, na.rm = TRUE),
    # including date of uk entry code
    median_time_from_1st_pracreg_first_migration_code_days_withdoe = median(time_from_1st_pracreg_first_migration_code_days, na.rm = TRUE),
    q25_time_from_1st_pracreg_first_migration_code_days_withdoe = quantile(time_from_1st_pracreg_first_migration_code_days, 0.25, na.rm = TRUE),
    q75_time_from_1st_pracreg_first_migration_code_days_withdoe = quantile(time_from_1st_pracreg_first_migration_code_days, 0.75, na.rm = TRUE),
    median_time_from_1st_pracreg_first_migration_code_months_withdoe = median(time_from_1st_pracreg_first_migration_code_months , na.rm = TRUE),
    q25_time_from_1st_pracreg_first_migration_code_months_withdoe = quantile(time_from_1st_pracreg_first_migration_code_months , 0.25, na.rm = TRUE),
    q75_time_from_1st_pracreg_first_migration_code_months_withdoe = quantile(time_from_1st_pracreg_first_migration_code_months , 0.75, na.rm = TRUE),
    median_time_from_birth_first_migration_code_days_withdoe = median(time_from_birth_first_migration_code_days, na.rm = TRUE),
    q25_time_from_birth_first_migration_code_days_withdoe = quantile(time_from_birth_first_migration_code_days, 0.25, na.rm = TRUE),
    q75_time_from_birth_first_migration_code_days_withdoe = quantile(time_from_birth_first_migration_code_days, 0.75, na.rm = TRUE),
    median_time_from_birth_first_migration_code_months_withdoe = median(time_from_birth_first_migration_code_months, na.rm = TRUE),
    q25_time_from_birth_first_migration_code_months_withdoe = quantile(time_from_birth_first_migration_code_months, 0.25, na.rm = TRUE),
    q75_time_from_birth_first_migration_code_months_withdoe = quantile(time_from_birth_first_migration_code_months, 0.75, na.rm = TRUE),
    # cob
    median_time_from_1st_pracreg_first_cob_code_days = median(time_from_1st_pracreg_first_cob_code_days, na.rm = TRUE),
    q25_time_from_1st_pracreg_first_cob_code_days = quantile(time_from_1st_pracreg_first_cob_code_days, 0.25, na.rm = TRUE),
    q75_time_from_1st_pracreg_first_cob_code_days = quantile(time_from_1st_pracreg_first_cob_code_days, 0.75, na.rm = TRUE),
    median_time_from_1st_pracreg_first_cob_code_months = median(time_from_1st_pracreg_first_cob_code_months , na.rm = TRUE),
    q25_time_from_1st_pracreg_first_cob_code_months = quantile(time_from_1st_pracreg_first_cob_code_months , 0.25, na.rm = TRUE),
    q75_time_from_1st_pracreg_first_cob_code_months = quantile(time_from_1st_pracreg_first_cob_code_months , 0.75, na.rm = TRUE),
    # english language
    median_time_from_1st_pracreg_first_language_code_days = median(time_from_1st_pracreg_first_language_code_days, na.rm = TRUE),
    q25_time_from_1st_pracreg_first_language_code_days = quantile(time_from_1st_pracreg_first_language_code_days, 0.25, na.rm = TRUE),
    q75_time_from_1st_pracreg_first_language_code_days = quantile(time_from_1st_pracreg_first_language_code_days, 0.75, na.rm = TRUE),
    median_time_from_1st_pracreg_first_language_code_months = median(time_from_1st_pracreg_first_language_code_months , na.rm = TRUE),
    q25_time_from_1st_pracreg_first_language_code_months = quantile(time_from_1st_pracreg_first_language_code_months , 0.25, na.rm = TRUE),
    q75_time_from_1st_pracreg_first_language_code_months = quantile(time_from_1st_pracreg_first_language_code_months , 0.75, na.rm = TRUE),
    # interpreter
    median_time_from_1st_pracreg_first_interpreter_code_days = median(time_from_1st_pracreg_first_interpreter_code_days, na.rm = TRUE),
    q25_time_from_1st_pracreg_first_interpreter_code_days = quantile(time_from_1st_pracreg_first_interpreter_code_days, 0.25, na.rm = TRUE),
    q75_time_from_1st_pracreg_first_interpreter_code_days = quantile(time_from_1st_pracreg_first_interpreter_code_days, 0.75, na.rm = TRUE),
    median_time_from_1st_pracreg_first_interpreter_code_months = median(time_from_1st_pracreg_first_interpreter_code_months , na.rm = TRUE),
    q25_time_from_1st_pracreg_first_interpreter_code_months = quantile(time_from_1st_pracreg_first_interpreter_code_months , 0.25, na.rm = TRUE),
    q75_time_from_1st_pracreg_first_interpreter_code_months = quantile(time_from_1st_pracreg_first_interpreter_code_months , 0.75, na.rm = TRUE),
    # immigration status excl refugee
    median_time_from_1st_pracreg_first_immig_status_excl_refugee_code_days = median(time_from_1st_pracreg_first_immig_status_excl_refugee_code_days, na.rm = TRUE),
    q25_time_from_1st_pracreg_first_immig_status_excl_refugee_code_days = quantile(time_from_1st_pracreg_first_immig_status_excl_refugee_code_days, 0.25, na.rm = TRUE),
    q75_time_from_1st_pracreg_first_immig_status_excl_refugee_code_days = quantile(time_from_1st_pracreg_first_immig_status_excl_refugee_code_days, 0.75, na.rm = TRUE),
    median_time_from_1st_pracreg_first_immig_status_excl_refugee_code_months = median(time_from_1st_pracreg_first_immig_status_excl_refugee_code_months , na.rm = TRUE),
    q25_time_from_1st_pracreg_first_immig_status_excl_refugee_code_months = quantile(time_from_1st_pracreg_first_immig_status_excl_refugee_code_months , 0.25, na.rm = TRUE),
    q75_time_from_1st_pracreg_first_immig_status_excl_refugee_code_months = quantile(time_from_1st_pracreg_first_immig_status_excl_refugee_code_months , 0.75, na.rm = TRUE),
    # refugee and asylum
    median_time_from_1st_pracreg_first_refugee_code_days = median(time_from_1st_pracreg_first_refugee_code_days, na.rm = TRUE),
    q25_time_from_1st_pracreg_first_refugee_code_days = quantile(time_from_1st_pracreg_first_refugee_code_days, 0.25, na.rm = TRUE),
    q75_time_from_1st_pracreg_first_refugee_code_days = quantile(time_from_1st_pracreg_first_refugee_code_days, 0.75, na.rm = TRUE),
    median_time_from_1st_pracreg_first_refugee_code_months = median(time_from_1st_pracreg_first_refugee_code_months , na.rm = TRUE),
    q25_time_from_1st_pracreg_first_refugee_code_months = quantile(time_from_1st_pracreg_first_refugee_code_months , 0.25, na.rm = TRUE),
    q75_time_from_1st_pracreg_first_refugee_code_months = quantile(time_from_1st_pracreg_first_refugee_code_months , 0.75, na.rm = TRUE),
    # trafficking
    median_time_from_1st_pracreg_first_trafficking_code_days = median(time_from_1st_pracreg_first_trafficking_code_days, na.rm = TRUE),
    q25_time_from_1st_pracreg_first_trafficking_code_days = quantile(time_from_1st_pracreg_first_trafficking_code_days, 0.25, na.rm = TRUE),
    q75_time_from_1st_pracreg_first_trafficking_code_days = quantile(time_from_1st_pracreg_first_trafficking_code_days, 0.75, na.rm = TRUE),
    median_time_from_1st_pracreg_first_trafficking_code_months = median(time_from_1st_pracreg_first_trafficking_code_months , na.rm = TRUE),
    q25_time_from_1st_pracreg_first_trafficking_code_months = quantile(time_from_1st_pracreg_first_trafficking_code_months , 0.25, na.rm = TRUE),
    q75_time_from_1st_pracreg_first_trafficking_code_months = quantile(time_from_1st_pracreg_first_trafficking_code_months , 0.75, na.rm = TRUE),
    # uk cob
    median_time_from_1st_pracreg_first_uk_cob_code_days = median(time_from_1st_pracreg_first_uk_cob_code_days, na.rm = TRUE),
    q25_time_from_1st_pracreg_first_uk_cob_code_days = quantile(time_from_1st_pracreg_first_uk_cob_code_days, 0.25, na.rm = TRUE),
    q75_time_from_1st_pracreg_first_uk_cob_code_days = quantile(time_from_1st_pracreg_first_uk_cob_code_days, 0.75, na.rm = TRUE),
    median_time_from_1st_pracreg_first_uk_cob_code_months = median(time_from_1st_pracreg_first_uk_cob_code_months , na.rm = TRUE),
    q25_time_from_1st_pracreg_first_uk_cob_code_months = quantile(time_from_1st_pracreg_first_uk_cob_code_months , 0.25, na.rm = TRUE),
    q75_time_from_1st_pracreg_first_uk_cob_code_months = quantile(time_from_1st_pracreg_first_uk_cob_code_months , 0.75, na.rm = TRUE),
    .groups = "drop"
  ) 

dir_create(path_dir(output_file))
write_csv(migration_coding_summary, path = output_file)