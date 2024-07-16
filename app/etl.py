#%%
import polars as pl
import pandas as pd
import sqlite3
import os
import glob
import re
from PIL import Image
import io
from thefuzz import process,fuzz


#%%
# create db connection
db_name = 'countries.db'

db_conn = sqlite3.connect(db_name)
db_cursor = sqlite3.Cursor(db_conn)

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
# join city and country data
capitals_with_coordinates = capitals_df.join(cities_df[['city','country','latitude','longitude','population','elevation']],how='left',on = ['city','country'])

# add combined data to database, schema on write
capitals_with_coordinates = capitals_with_coordinates.with_columns(pl.lit(None).alias('flag'))

#%%
#add sdc coordinates
capitals_with_coordinates_sdc = capitals_with_coordinates.filter(pl.col('latitude').is_not_null()).with_columns(pl.col('longitude').str.replace('E','').str.replace('W','-').alias('longitude_sdc'),pl.col('latitude').str.replace('S','-').str.replace('N','').alias('latitude_sdc')).with_columns((pl.col('latitude_sdc') + ',' + pl.col('longitude_sdc') + ',' + pl.col('city')).alias('coords_city_sdc'))

#write country data to the db
capitals_with_coordinates_sdc.write_database(table_name='country_info',connection=f'sqlite:///{db_name}',if_table_exists='replace')

#create flags table
drop_table_sql = f'''DROP TABLE IF EXISTS flags;'''
create_table_sql = f'''CREATE TABLE flags (country VARCHAR(200), flag BLOB);'''
try:
    db_cursor.execute(drop_table_sql)
    db_cursor.execute(create_table_sql)
    db_conn.commit()
    print('Table created')
except:
    print('Cannot create table, check that you don"t have any errors in your code')

# add flags to database
path = 'app/flags'
flags_list = []
filenames = glob.glob(f'{path}/*.svg.png')
flags_dict = {}
# change the path slashes, unix to windows
filenames = [f.replace('\\','/') for f in filenames]

# load all the flags into the database
for file in filenames:
    try:
        with open(file,'rb') as f:
            # get rid of dots and square brackets, create country and flag pair
            flags_dict = {'country':re.split('[/.\\[\\]]',file)[2],'flag': f.read()}
        insert_data_sql = '''INSERT INTO flags (country,flag) VALUES (?,?);'''
        db_cursor.execute(insert_data_sql,(flags_dict['country'],flags_dict['flag']))
        print(f'added {flags_dict['country']}')
    except:
        print(f'Could not read {file}')


pl.read_database('SELECT * FROM flags',db_conn)

#%%
# create countries ref table, fuzzy match to fix issue with flags table
flags_df = pl.read_database('SELECT country FROM flags',db_conn)
countries_ref_df = capitals_df.select(['country'])

#TODO create join on join table for flag names
countries_ref_df.map_rows(lambda x: (process.extractOne(x[0],flags_df['country'],scorer=fuzz.token_set_ratio))[0] + ';' + x[0]).select(pl.col('map').str.split(';'))


#%%
try:
    join_tables = f'''UPDATE country_info SET flag = (SELECT flag FROM flags WHERE (country_info.country = flags.country))'''
    db_cursor.execute(join_tables)
    db_conn.commit()
    print('The country_info table ws updated with flags succesfully')
except:
    db_conn.rollback()
    print('Had to rollback, could not update country_info table with flags')

#%%
pl.read_database('SELECT * FROM flags',db_conn)

pl.read_database('SELECT * FROM country_info where flag IS NOT NULL',db_conn)

# %%
db_conn.close()
# %%
