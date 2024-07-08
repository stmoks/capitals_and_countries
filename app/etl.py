#%%
import pandas as pd
import polars as pl
import sqlite3
import os
import glob
import re


# create db connection
db_name = 'countries.db'

# try:
#     os.remove(db_name)
#     print('The database has been successfully removed')
# except Exception as e:
#     print(f'The database could not be removed. Please consider whether it exists and try again \n{e}')

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
# add base data
capitals_with_coordinates = capitals_df.join(cities_df[['city','country','latitude','longitude','population','elevation']],how='left',on = ['city','country'])


# add flags to database
path = 'flags'
flags_list = []
filenames = glob.glob(f'{path}/*.svg.png')
flags_dict = {}

create_table_sql = f'''CREATE TABLE flags (country VARCHAR(200), flag BLOB);'''
try:
    db_cursor.execute(create_table_sql)
except:
    print('Cannot create table, it might already exist')


# change the path slashes, unix to windows
filenames = [f.replace('\\','/') for f in filenames]
for file in filenames[0:3]:
    try:
        flags_dict = {'country':re.split('[/.\\[\\]]',file)[1],'flag': file}
        insert_data_sql = f'''INSERT INTO flags (country,flag) VALUES ({flags_dict['country']},{flags_dict['flag']});'''
        db_cursor.execute(insert_data_sql)
        print(f'added {flags_dict['country']}')
    except:
        print(f'Could not read {file}')


capitals_with_flags = capitals_with_coordinates.join(flags_dict,left_on='country',right_on='country')
# create table - schema on write, flexible data types
create_table_sql = f'''
CREATE TABLE country_info ({capitals_with_coordinates.columns};)
'''
db_cursor.execute(create_table_sql)

add_column_sql = '''ALTER TABLE country_info ADD COLUMN flags;'''
db_cursor.execute(add_column_sql)



db_conn.close()

# %%
