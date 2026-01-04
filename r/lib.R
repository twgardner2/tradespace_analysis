library(sf)
library(nngeo)

make_sensor_feasibility_plot_myOriginalThatSucked <- function(model_output, PLOTS_OUTPUT_PATH, filename) {
  # I want to keep this in the repo as an example of how I used Gen AI to 
  # improve one of my plots
  
  df <- model_output %>% 
    select(
      valid, altitude_kft, mach, sensor
    )
  
  h_unique <- unique(df$mach)
  v_unique <- unique(df$altitude_kft)
  h_binwidth <- h_unique[2]-h_unique[1]
  v_binwidth <- v_unique[2]-v_unique[1]
  
  alpha <- 0.7
  
  p <- ggplot(
    data=df %>% filter(valid) %>% mutate(sensor=forcats::fct_rev(sensor)),
    mapping=aes(x=mach, y=altitude_kft, fill=sensor)
  ) +
    # facet_wrap(~sensor) +
    
    geom_tile(data=df %>% filter(valid, sensor=='HIGH'), width = h_binwidth, height = v_binwidth, alpha=alpha, color='black', linewidth = 0.08) +
    geom_tile(data=df %>% filter(valid, sensor=='MED'), width = h_binwidth, height = v_binwidth, alpha=alpha, color='black', linewidth = 0.08) +
    geom_tile(data=df %>% filter(valid, sensor=='LOW'), width = h_binwidth, height = v_binwidth, alpha=alpha) +
    
    scale_fill_manual(values=sensor_color_scale)  +
    labs(
      title='Mach/Altitude Feasibility Envelope by Sensor',
      x='Mach',
      y='Altitude (kft)',
      fill='Sensor Type',
      color='Sensor Type'
    )
  ggsave(filename = file.path(PLOTS_OUTPUT_PATH, filename))
  return(p)
}

make_sensor_feasibility_plot <- function(
    model_output, 
    sensor_color_scale,
    ALTITUDE_BOUNDS,
    MACH_BOUNDS,
    PLOTS_OUTPUT_PATH, 
    filename
  ) {

  HEIGHT = 4
  ASPECT_RATIO = 0.6
  
  df <- model_output %>% 
    select(
      altitude_kft, mach, sensor
    )
  
  sensors_present <- unique(df$sensor)
  active_colors <- sensor_color_scale[names(sensor_color_scale) %in% sensors_present]
  
  if(nrow(df) <= 0) {
    
    p <- ggplot() +
      geom_blank()
    
  } else {
    
    # 1. Convert tiles to spatial polygons
    h_unique <- unique(df$mach)
    v_unique <- unique(df$altitude_kft)
    h_half <- (h_unique[2]-h_unique[1])/2
    v_half <- (v_unique[2]-v_unique[1])/2
    
    tiles_sf <- df %>% 
      mutate(
        # Create the 4 corners of each tile
        geometry = purrr::pmap(list(mach, altitude_kft), ~ {
          m <- ..1; a <- ..2
          st_polygon(list(matrix(c(
            m-h_half, a-v_half,
            m+h_half, a-v_half,
            m+h_half, a+v_half,
            m-h_half, a+v_half,
            m-h_half, a-v_half
          ), ncol = 2, byrow = TRUE)))
        })
      ) %>%
      st_as_sf()
    
    # 2. Robust Dissolve
    outlines_sf <- tiles_sf %>%
      group_by(sensor) %>%
      # A tiny buffer solves 99% of internal line issues
      st_buffer(dist = 1e-8) %>% 
      summarize(geometry = st_union(geometry)) %>%
      st_make_valid() %>%
      # Optional: Remove any internal 'holes' if you only want the outer shell
      nngeo::st_remove_holes() %>% 
      st_cast("MULTILINESTRING")
  
    # 3. Plot with Polished Legend
    p <- ggplot() +
      # Background Tiles
      geom_tile(data = df, 
                aes(x = mach, y = altitude_kft, fill = sensor), alpha = 0.3) +
      
      # Outer Outlines - use key_glyph = "rect" to force the legend shape
      geom_sf(data = outlines_sf, aes(color = sensor), 
              linewidth = 1, inherit.aes = FALSE, key_glyph = "rect") 
  }
  
  p +
    
    # Combine Fill and Color into one legend by giving them the same title
    scale_fill_manual(values = active_colors, name = "Sensor Type") +
    scale_color_manual(values = active_colors, name = "Sensor Type") +
    
    labs(
      title = 'Mach/Altitude Feasibility Envelope by Sensor',
      x     = "Mach",
      y     = "Altitude (kft)"
    ) +
    
    # Override the legend appearance to show the border and fill correctly
    guides(
      fill = guide_legend(
        override.aes = list(
          # Set the transparency and border color/width for the legend box
          alpha = 0.8,           # Transparency of the fill
          # color = active_colors, # Border color
          linewidth = 1          # Thickness of the border line
        )
      ),
      color = "none" # Hide the secondary color legend to avoid duplication
    ) +
    
    coord_sf(
      expand = TRUE,
      xlim   = MACH_BOUNDS,
      ylim   = ALTITUDE_BOUNDS
    ) + 

    theme_minimal() + 
    theme(
      plot.title = element_text(hjust = 0.5),
      aspect.ratio = ASPECT_RATIO,
      panel.grid.major = element_line(color = "gray90", linewidth = 0.2),
      panel.grid.minor = element_blank(),
      legend.key = element_rect(fill = "white", color = NA) # Clean background for keys
    )
  
  ggsave(
    filename = file.path(PLOTS_OUTPUT_PATH, filename),
    height = HEIGHT, 
    width = HEIGHT / ASPECT_RATIO
  )
  return(p)
}

make_cost_heatmap <- function(
    df, 
    sensor_color_scale, 
    ALTITUDE_BOUNDS,
    MACH_BOUNDS,
    PLOTS_OUTPUT_PATH, 
    filename
  ) {
  
  ALPHA = 1
  HEIGHT = 4
  ASPECT_RATIO = 0.6
  
  out_path <- file.path(PLOTS_OUTPUT_PATH, filename)
  
  df <- df %>% 
    select(
      altitude_kft, mach, sensor, onsta_req_cost
    ) 

  # ONSTA Aircraft Cost ----
  h_unique <- unique(df$mach)
  v_unique <- unique(df$altitude_kft)
  h_binwidth <- h_unique[2]-h_unique[1]
  v_binwidth <- v_unique[2]-v_unique[1]
  
  p <- ggplot(
      data=df,
      mapping=aes(x=mach, y=altitude_kft, fill=onsta_req_cost)
    ) +
      
    geom_tile(width = h_binwidth, height = v_binwidth, alpha=ALPHA) +

    facet_wrap(~sensor) +
    
    scale_x_continuous(limits = MACH_BOUNDS) +
    scale_y_continuous(limits = ALTITUDE_BOUNDS) +

    scale_fill_gradientn(
      colors = c("green", "white", "red"),
      transform = 'log10'
    ) +
    
    labs(
      title='ONSTA Aircraft Cost by Sensor',
      x='Mach',
      y='Altitude (kft)',
      fill='Cost ($M)',
      color='Sensor Type'
    ) +
    
    theme_minimal()
  
  p
  ggsave(
    filename = out_path,
    height = HEIGHT,
    width = HEIGHT / ASPECT_RATIO
  )
  return(p)

  
}


calc_elasticity <- function(
    data         = df,
    obj_var      = 'onsta_req_cost',
    elastic_var,
    doe_vars     = c('altitude_kft', 'sensor', 'mach') 
  ) {

  constant_vars <- setdiff(doe_vars, elastic_var)
  
  if(elastic_var == 'sensor') {
    elastic_var <- 'sensor_assumption_cost'
  }

  data <- data %>% 
    group_by(across(all_of(constant_vars))) %>% 
    arrange(across(all_of(c(constant_vars, elastic_var)))) %>% 
    mutate(
      elasticity = if_else(
        lag(.data[[obj_var]]) > 0 & lag(.data[[elastic_var]]) > 0 ,
        
        ((.data[[obj_var]] - lag(.data[[obj_var]])) / lag(.data[[obj_var]])) /
        ((.data[[elastic_var]] - lag(.data[[elastic_var]])) / lag(.data[[elastic_var]])),
        
        NA_real_
      )
    ) %>% 
    ungroup()
    
  return(data$elasticity)
}
