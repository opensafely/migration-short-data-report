###################################################
# This script creates descriptive demographic tables for the overall full cohort by migration code type
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
output_file <- "output/tables/demographics_full_study_cohort_migration_types.csv"

# Import data ----
cohort <- read_feather(cohort_file) %>%
  mutate(
    across(
      where(is.ordered),
      ~ factor(as.character(.x))
    )
  )

migration_type_vars <- c("any_migrant", 
                         "not_born_in_uk", 
                         "immig_status_excl_refugee_asylum", 
                         "refugee_asylum_status",
                         "english_not_main_language",
                         "interpreter_required",
                         "trafficking",
                         "british_ethnicities",
                         "born_in_uk")
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

summarise_variable <- function(cohort, var) {
  cohort <- cohort %>%
    filter(.data[[var]] == TRUE)
  
  table_freq_overall <- tibble::tibble(
    subgroup = "All",
    category = "All",
    n = rounding(nrow(cohort)),
    percentage = 100
  ) %>%
    mutate(cohort_variable_description = var)

table_freq <- 
  cohort %>%
    pivot_longer(
      cols = all_of(vars_to_summarise),
      names_to = "subgroup",
      values_to = "category"
    ) %>%
    count(
      subgroup,
      category,
      name = "n") %>%
  group_by(subgroup) %>%
  mutate(
    category = fct_explicit_na(category, "unknown"),
    n = rounding(n),
    percentage = round((100 * n / sum(n, na.rm = TRUE)),1),
  ) %>%
  ungroup() %>%
  mutate(cohort_variable_description = var)

bind_rows(table_freq_overall,
                        table_freq)
}

results <- lapply(migration_type_vars, function(var){
  summarise_variable(cohort,var)
}) %>%
  bind_rows()

dir_create(path_dir(output_file))
write_csv(results, path = output_file)


