library(tidyverse)
library(RColorBrewer)


source('./r/lib.R')

if(!interactive()) pdf(NULL)

# Paths
PLOTS_OUTPUT_PATH <- file.path(getwd(), 'output/plots')


# Read data
df <- readr::read_csv('./output/model_output.csv') 

# Clean data
names(df) <- gsub('config_', '', names(df))
df <- df %>% 
  mutate(
    sensor = stringr::str_remove(sensor, 'Sensor.'),
    sensor = factor(sensor, levels=c('LOW', 'MED', 'HIGH'))
  )


# Visualize data
sensor_color_scale <- RColorBrewer::brewer.pal(3, 'Dark2')

## Feasibility plot

p1 <- make_sensor_feasibility_plot_myOriginalThatSucked(
  df, 
  PLOTS_OUTPUT_PATH,
  'sensor_feasibility_original.png'
)


p2 <- make_sensor_feasibility_plot(
  df,
  PLOTS_OUTPUT_PATH,
  'sensor_feasibility.png'
)




# ggsave('sensor_v_cost.png')
