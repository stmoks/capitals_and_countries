#%%
import polars as pl
import pandas as pd
import sqlite3
import os
import glob
import re
from PIL import Image
import io


#%%
# create db connection
db_name = 'capitals and countries.db'

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


# add sdc coordinates
capitals_with_coordinates_sdc = capitals_with_coordinates.filter(pl.col('latitude').is_not_null()).with_columns(pl.col('longitude').str.replace('E','').str.replace('W','-').alias('longitude_sdc'),pl.col('latitude').str.replace('S','-').str.replace('N','').alias('latitude_sdc')).with_columns((pl.col('latitude_sdc') + ',' + pl.col('longitude_sdc') + ',' + pl.col('city')).alias('coords_city_sdc'))

#%%
# write country info to the db
capitals_with_coordinates_sdc.write_database(table_name='country_info',connection=f'sqlite:///{db_name}',if_table_exists='replace')
#%%
#create flags table
drop_table_sql = f'''DROP TABLE IF EXISTS flags;'''
create_table_sql = f'''CREATE TABLE flags (country VARCHAR(200), flag BLOB);'''
try:
    db_cursor.execute(drop_table_sql)
    db_cursor.execute(create_table_sql)
    db_conn.commit()
    print('Table created')
except Exception as e:
    print('Cannot create table:',e)

# add flags to database
path = 'flags'
flags_list = []
filenames = glob.glob(f'{path}/*.svg.png')
flags_dict = {}
# change the path slashes, unix to windows
filenames = [f.replace('\\','/') for f in filenames]

# load all the flags into the database
for file in filenames:
    flag_counter = 0
    try:
        with open(file,'rb') as f:
            # get rid of dots and square brackets, create country and flag pair
            flags_dict = {'country':re.split('[/.\\[\\]]',file)[1],'flag': f.read()}
        insert_data_sql = '''INSERT INTO flags (country,flag) VALUES (?,?);'''
        db_cursor.execute(insert_data_sql,(flags_dict['country'],flags_dict['flag']))
        flag_counter += 1
        db_conn.commit()
    except Exception as e:
        print(f'Could not read {file}:',e)
print(f'succesfully added {flag_counter} countries')

pl.read_database('SELECT * FROM flags',db_conn)

#%%
# load country mapping
country_mapping = pl.read_csv('country_mapping_utf8.csv')

# can't write to sqllite directly with polars, so use sqlalchemy connection
country_mapping.write_database('country_mapping',connection = f'sqlite:///{db_name}',if_table_exists = 'replace',engine='adbc')

pl.read_database('SELECT * FROM country_mapping',db_conn)


#%%
try:
    try:
        add_column = f'''ALTER TABLE country_info ADD flag_country_reference VARCHAR;'''
        db_cursor.execute(add_column)
    except Exception as e:
        print('Could not add column:',e)
    join_tables = f'''UPDATE country_info SET flag_country_reference = (SELECT flag_country_reference FROM country_mapping WHERE (country_info.country = country_mapping.wiki_country_reference))'''
    db_cursor.execute(join_tables)
    pl.read_database('SELECT * FROM country_info',db_conn)
    join_tables = f'''UPDATE country_info SET flag = (SELECT flag FROM flags WHERE (country_info.country = flags.country))'''
    db_cursor.execute(join_tables)
    db_conn.commit()
    print('The country_info table ws updated with flags succesfully')
except Exception as e:
    db_conn.rollback()
    print('Had to rollback, could not update country_info table with flags')

#%%
pl.read_database('SELECT * FROM flags',db_conn)

pl.read_database('SELECT * FROM country_info where flag IS NOT NULL',db_conn)

# %%
db_conn.close()
# %%
