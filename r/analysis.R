library(tidyverse)

df <- readr::read_csv('./output/model_output.csv') 
names(df) <- gsub('config_', '', names(df))
df <- df %>% 
  mutate(
    sensor = stringr::str_remove(sensor, 'Sensor.'),
    sensor = factor(sensor, levels=c('LOW', 'MED', 'HIGH'))
  )
print(names(df))

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
