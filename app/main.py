#%%
import pandas as pd
import polars as pl
import unidecode
import sqlite3
import folium
from PIL import Image

#%%

# create database connection
db_name = 'capitals and countries.db'


db_conn = sqlite3.connect(db_name)
db_cursor = sqlite3.Cursor(db_conn)


# %%

m = folium.Map(location=[-29, 25], 
    zoom_start= 5)

#TODO acknowledging the other connection, but not this
country_info = pl.read_database('SELECT * FROM country_info where flag IS NOT NULL',db_conn)

#%%
y=country_info.select(pl.col('flag'))[0,0]

# Image.open('flags/Armenia.svg.png')

# def show_flag(flag):
#     with open(file=flag,mode='rb') as file:
#         output = Image.open(file)
#     return output
# show_flag(y)

#%%
#TODO show the flags on the popup 
country_info.with_columns(
    pl.col('coords_city_sdc').map_elements(lambda x: folium.CircleMarker(location = x.split(',')[0:2], radius=0.5,
    fill=True,
    popup=country_info.filter(pl.col('city')== x.split(',')[2]).select(pl.col(['country','city']))._repr_html_()).add_to(m)))
m

# select(pl.col('flag').map_elements(lambda x: Image.open(x))).


# %%
