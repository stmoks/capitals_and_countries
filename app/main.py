#%%
import pandas as pd
import polars as pl
import unidecode
import sqlite3
from sqlalchemy import create_engine
import geopandas as gp
import folium


# read data from Wikipedia
#%%
capitals_url = 'https://en.wikipedia.org/wiki/List_of_national_capitals'
list_of_tables = pd.read_html(capitals_url)
capitals_df = list_of_tables[1]

cities_url = 'https://en.wikipedia.org/wiki/List_of_cities_by_elevation'
list_of_tables = pd.read_html(cities_url)
cities_df = list_of_tables[1]


#%%
capitals_df


#%%
# change column names
capitals_df = pl.from_pandas(capitals_df,rechunk=True)
capitals_df = capitals_df.rename({'City/Town':'city','Country/Territory':'country','Continent':'continent','Notes':'notes'})
#%%
cities_df = pl.from_pandas(cities_df,rechunk=True)
cities_df = cities_df.rename({'City Name/s':'city','Country/Territory':'country','Continental Region':'continent','Population':'population','Latitude':'latitude','Longitude':'longitude','Elevation (m)':'elevation'})
cities_df


#%%
# extract all the data before the extra information (brackets in this case)
# remove special characters from the city and country names so we can join two datasets later
capitals_df = capitals_df.with_columns(
    pl.col('city').str.replace(r'\s*\(.*', '').replace(r'[\',.]',''),
    pl.col('country').str.replace(r'\s*\(.*', '').replace(r'[\',.]',''),
    pl.col('city').str.extract(r'\s*\(.*',0).str.strip_chars(' ()').alias('city_extra_info')
)

cities_df = cities_df.with_columns(
    pl.col('city').str.replace(r'\s*\(.*', '').replace(r'[\',.]',''),
    pl.col('country').str.replace(r'\s*\(.*', '').replace(r'[\',.]',''),
    pl.col('elevation').str.replace(r'\s*\(.*', '').replace(r'[\',.]',''),

    )

countries_df = cities_df['country']

#%%
# join so we can use geo pandas
capitals_with_coordinates = capitals_df.join(cities_df[['city','country','latitude','longitude','population','elevation']],how='left',on = ['city','country'])


#%%
# get info about the new dataframe
print(capitals_with_coordinates.glimpse())
# %%

capitals_with_coordinates_sdc = capitals_with_coordinates.filter(pl.col('latitude').is_not_null()).with_columns(pl.col('longitude').str.replace('E','').str.replace('W','-').alias('latitude_sdc'),pl.col('latitude').str.replace('S','-').str.replace('N','').alias('longitude_sdc')).with_columns((pl.col('latitude_sdc') + ',' + pl.col('longitude_sdc')).alias('coords_sdc'))

m = folium.Map(location=[20, 0])

capitals_with_coordinates_sdc['coords_sdc'].map_elements(lambda x: folium.Marker(x.split(',')[0:2]).add_to(m))
m


# %%
