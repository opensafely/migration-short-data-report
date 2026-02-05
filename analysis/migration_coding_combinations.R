###################################################
# This script describes the combinations of migration-related codes  
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
output_file <- "output/tables/migration_code_combinations_summary.csv"

# Import data ----
cohort <- read_feather(cohort_file) %>%
  mutate(
    across(
      where(is.ordered),
      ~ factor(as.character(.x))
    )
  )

# rounding function taken from: https://github.com/opensafely/death-report/blob/main/analysis/Table_DoD.R (accessed 19/01/26)
rounding <- function(vars) {
  case_when(vars == 0 ~ 0,
            vars > 7 ~ round(vars / 5) * 5)
}

migration_code_combinations_summary <- cohort %>%
  rowwise() %>%
  mutate(
    migrant_concat = paste(
      c(if (not_born_in_uk) "not_born_in_uk",
        if (immig_status_excl_refugee_asylum) "immig_status_excl_refugee_asylum",
        if (refugee_asylum_status) "refugee_asylum_status",
        if (english_not_main_language) "english_not_main_language",
        if (interpreter_required) "interpreter_required"
      ),
      collapse = "; "
    ),
    migrant_concat = if_else(
      migrant_concat == "",
      "no_migration_codes",
      migrant_concat)) %>%
  ungroup() %>%
  group_by(migrant_concat) %>%
  summarise(total = rounding(n()))
  
dir_create(path_dir(output_file))
write_csv(migration_code_combinations_summary, path = output_file)

