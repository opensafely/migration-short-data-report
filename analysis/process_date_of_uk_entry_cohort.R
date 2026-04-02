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

cohort_file <- "output/cohorts/date_of_entry_cohort.arrow"
output_file <- "output/tables/demographics_date_of_uk_entry_cohort.csv"

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

table_freq_overall <- cohort %>%
  group_by(any_migrant) %>%
  summarise(
    n = rounding(nrow(cohort)),
    percentage = 100) %>%
  mutate(
    subgroup = "All",
    category = "All"
  )

table_freq <- cohort %>%
  pivot_longer(
    cols = all_of(vars_to_summarise),
    names_to = "subgroup",
    values_to = "category"
  ) %>%
  group_by(any_migrant, subgroup
  ) %>%
  count(
    category,
    name = "n"
  ) %>%
  mutate(
    category = fct_explicit_na(category, "unknown"),
    n = rounding(n),
    percentage = round((100 * n / sum(n, na.rm = TRUE)),1)
  ) %>%
  ungroup() 

table_freq <- bind_rows(table_freq_overall, table_freq)
table_freq <- table_freq %>%
  relocate(n, .before= percentage)

dir_create(path_dir(output_file))
write_csv(table_freq, path = output_file)

