library(tidyverse)
library(RColorBrewer)


if(!interactive()) pdf(NULL)


# Read data
df <- readr::read_csv('./output/model_output.csv') 

# Clean data
names(df) <- gsub('config_', '', names(df))
df <- df %>% 
  mutate(
    sensor = stringr::str_remove(sensor, 'Sensor.'),
    sensor = factor(sensor, levels=c('LOW', 'MED', 'HIGH'))
  )
print(names(df))


# Visualize data
sensor_color_scale <- RColorBrewer::brewer.pal(3, 'Dark2')

## Feasibility plot
h_unique <- unique(df$mach)
v_unique <- unique(df$altitude_kft)
h_binwidth <- h_unique[2]-h_unique[1]
v_binwidth <- v_unique[2]-v_unique[1]
alpha <- 0.8
p <- ggplot(
    data=df %>% filter(valid) %>% mutate(sensor=forcats::fct_rev(sensor)), 
    mapping=aes(x=mach, y=altitude_kft, fill=sensor)
  ) +
  # facet_wrap(~sensor) +
  
  # geom_tile(data=df %>% filter(valid, sensor=='HIGH'), width = h_binwidth, height = v_binwidth, fill='red', alpha=alpha ) +
  # geom_tile(data=df %>% filter(valid, sensor=='MED'), width = h_binwidth, height = v_binwidth, fill='green', alpha=alpha) +
  # geom_tile(data=df %>% filter(valid, sensor=='LOW'), width = h_binwidth, height = v_binwidth, fill='yellow', alpha=alpha)
  geom_tile(data=df %>% filter(valid, sensor=='HIGH'), width = h_binwidth, height = v_binwidth, alpha=alpha ) +
  geom_tile(data=df %>% filter(valid, sensor=='MED'), width = h_binwidth, height = v_binwidth, alpha=alpha) +
  geom_tile(data=df %>% filter(valid, sensor=='LOW'), width = h_binwidth, height = v_binwidth, alpha=alpha) +

  scale_fill_manual(values=sensor_color_scale)  

p


## Onsta aircraft cost 
p <- ggplot(data=df, mapping=aes(x=sensor, y=onsta_req_cost, fill=sensor)) +
  # geom_col(width=10) +
  # geom_point(size=2, shape=21) +
  geom_col() +
  scale_fill_manual(
    values = c('LOW'='blue', 'MED'='green', 'HIGH'='red')
  ) +
  facet_grid(altitude_kft~mach)
p

# ggsave('sensor_v_cost.png')
