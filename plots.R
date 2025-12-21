library(tidyverse)

setwd('/home/tom/Documents/interview/')

df <- readr::read_csv('./output.csv') %>% 
  mutate(sensor = factor(sensor, levels=c('Low', 'Med', 'High')))
# print(df)

p <- ggplot(data=df, mapping=aes(x=sensor, y=n_legs, fill=sensor)) +
  # geom_col(width=10) +
  geom_point(size=2, shape=21) +
  geom_col() +
  scale_fill_manual(
    values = c('Low'='blue', 'Med'='green', 'High'='red')
  ) +
  facet_grid(altitude~mach)
p

ggsave('sensor_v_cost.png')
