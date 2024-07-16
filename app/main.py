#%%
import pandas as pd
import polars as pl
import unidecode
import sqlite3
import folium


#%%
# create database connection
db_name = 'countries.db'


db_conn = sqlite3.connect(db_name)
db_cursor = sqlite3.Cursor(db_conn)


# %%

m = folium.Map(location=[-29, 25], 
    zoom_start= 5)

#TODO acknowledging the other connection, but not this
country_info = pl.read_database('SELECT * FROM country_info where flag IS NOT NULL',db_conn)


country_info.with_columns(
    pl.col('coords_city_sdc').map_elements(lambda x: folium.CircleMarker(location = x.split(',')[0:2], radius=15,
    fill=True,
    popup=country_info.filter(pl.col('city')== x.split(',')[2]).select('flag')._repr_html_()).add_to(m)))
m


# x.split(',')[2]

# %%
