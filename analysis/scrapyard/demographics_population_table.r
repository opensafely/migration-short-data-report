###############
## A script to generate the population denominator (including by sub-group)
## for the entire study period 
## Author: Yamina Boukari
################

library(here)

source(here("analysis", "lib", "utility.R"))

# load data
cohort <- read_feather("output/cohorts/population_denominator_cohort.arrow")

generate_demographics_table(
    cohort_file = cohort,
    output_file = "output/tables/demographics_population_denominator.csv"
)
