library(tidyverse)
library(RColorBrewer)


source('./r/lib.R')

if(!interactive()) pdf(NULL)

# Paths
PLOTS_OUTPUT_PATH <- file.path(getwd(), 'output/plots')


# Read data
df_raw <- readr::read_csv('./output/model_output.csv') 

# Clean data
df <- df_raw
## Clean names
names(df) <- gsub('config_', '', names(df))
df <- df %>% 
  mutate(
    sensor = stringr::str_remove(sensor, 'Sensor.'),
    sensor = factor(sensor, levels=c('LOW', 'MED', 'HIGH'))
  )

## Get bounds from unfiltered data to pass to plots
ALTITUDE_BOUNDS <- range(df$altitude_kft)
MACH_BOUNDS     <- range(df$mach)

## Filter out invalid/infeasible cases
df <- df %>% 
  filter(valid)


# Visualize data
sensor_color_scale <- RColorBrewer::brewer.pal(3, 'Dark2')
names(sensor_color_scale) <- unique(df$sensor)
## Feasibility plot
# 
# p1 <- make_sensor_feasibility_plot_myOriginalThatSucked(
#   df,
#   PLOTS_OUTPUT_PATH,
#   'sensor_feasibility_original.png'
# )


p2 <- make_sensor_feasibility_plot(
  df,
  sensor_color_scale,
  ALTITUDE_BOUNDS,
  MACH_BOUNDS,
  PLOTS_OUTPUT_PATH,
  'sensor_feasibility.png'
)


## Cost plots
p3 <- make_cost_heatmap(
  df, 
  sensor_color_scale, 
  ALTITUDE_BOUNDS,
  MACH_BOUNDS,
  PLOTS_OUTPUT_PATH, 
  'onsta_cost_by_mach_alt_sensor.png'
)

  
  

