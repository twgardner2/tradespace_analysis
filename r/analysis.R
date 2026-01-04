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

## Get data from unfiltered data to pass to plots
ALTITUDE_BOUNDS <- range(df$altitude_kft)
MACH_BOUNDS     <- range(df$mach)

AOI_INGRESS <- df$aoi_ingress[1]
AOI_EGRESS  <- df$aoi_egress[1]
AOI_WIDTH   <- df$aoi_width[1]
AOI_LENGTH  <- df$aoi_length[1]
AOI_REVISIT_TIME <- df$aoi_revisit_time_hr[1]

df <- df %>%
  ## Filter out invalid/infeasible cases
  filter(valid) %>%
  ## Keep columns required for analysis
  select(
    sensor,
    altitude_kft,
    mach,
    onsta_req_cost,
    onsta_req_n,
    sensor_assumption_cost
  )


# Visualize data
sensor_color_scale <- RColorBrewer::brewer.pal(3, 'Dark2')
names(sensor_color_scale) <- unique(df$sensor)
## Feasibility plot
p2 <- make_sensor_feasibility_plot(
  df,
  sensor_color_scale,
  ALTITUDE_BOUNDS,
  MACH_BOUNDS,
  PLOTS_OUTPUT_PATH,
  'sensor_feasibility.png'
)


# ## Cost plots
p3 <- make_cost_heatmap(
  df,
  sensor_color_scale,
  ALTITUDE_BOUNDS,
  MACH_BOUNDS,
  PLOTS_OUTPUT_PATH,
  'onsta_cost_by_mach_alt_sensor.png'
)

## Elasticity
df$elasticity_mach <- calc_elasticity(
  data        = df,
  elastic_var = 'mach'
)
df$elasticity_altitude_kft <- calc_elasticity(
  data        = df,
  elastic_var = 'altitude_kft'
)
df$elasticity_sensor <- calc_elasticity(
  data        = df, 
  elastic_var = 'sensor'
)

  
  
make_elasticity_heatmap(
    df,
    sensor_color_scale,
    ALTITUDE_BOUNDS,
    MACH_BOUNDS,
    PLOTS_OUTPUT_PATH,
    'elasticity.png'
)
