 library(ggplot2)
library(ggthemes)
library(RColorBrewer)
library(dplyr)
library(gridExtra)
library(readr)

area <- read_delim("/home/anmabur/fotos_tmp/data_area.csv", ";", 
    escape_double = FALSE, trim_ws = TRUE)
area$DATE <- as.Date(as.character(area$DATE), "%Y%m%d")
theme_set(theme_bw())
area <- area[(area$"CLOUD(%)" < 35) & (area$"CLOUD(%)" != 0),]
ggplot(area,aes(x=DATE)) +
          geom_point(aes(y=`RESERVOIRAREA(ha)`, color = `RESERVOIRAREA(ha)`)) +
          geom_smooth(span = 0.3, aes(y=`RESERVOIRAREA(ha)`)) +
          scale_x_date(name="Date", date_breaks = "3 month", date_minor_breaks = "1 month", date_labels = "%B %Y") +
          scale_y_continuous(name="Reservoir area (ha)", labels = function(x) format(x, scientific = FALSE)) +
          scale_color_gradient(low = "brown", high = "green") +
          labs(color = "", title = "Iznajar reservoir (2018-2019)")+ theme(legend.position = "none")

ggsave("/home/anmabur/fotos_tmp/data.png", width = 8.0, height = 5.0, units = "in")
