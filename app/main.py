#%%
import pandas as pd
import polars as pl
import unidecode
import sqlite3
import folium


#%%
conn = sqlite3.connect('capitals_db')

country_info = 
# get info about the new dataframe
print(capitals_with_coordinates.glimpse())
# %%

capitals_with_coordinates_sdc = capitals_with_coordinates.filter(pl.col('latitude').is_not_null()).with_columns(pl.col('longitude').str.replace('E','').str.replace('W','-').alias('longitude_sdc'),pl.col('latitude').str.replace('S','-').str.replace('N','').alias('latitude_sdc')).with_columns((pl.col('latitude_sdc') + ',' + pl.col('longitude_sdc') + ',' + pl.col('city')).alias('coords_city_sdc'))

m = folium.Map(location=[-29, 25], 
    zoom_start= 5)



capitals_with_coordinates_sdc.with_columns(
    pl.col('coords_city_sdc').map_elements(lambda x: folium.CircleMarker(location = x.split(',')[0:2], radius=15,
    fill=True,
    popup=capitals_with_coordinates_sdc.filter(pl.col('city')== x.split(',')[2]).select('country')._repr_html_()).add_to(m)))
m


# x.split(',')[2]

# %%
