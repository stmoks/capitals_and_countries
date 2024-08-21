#%%
import polars as pl
import pandas as pd
import os
import glob
import re
import io
from sqlalchemy import create_engine,text


#%%
# create db connection
# db_name = 'capitals and countries.db'
db_conn_dict = {
    'db_name': 'dumela',
    'schema_name': 'users',
    'username': 'postgres',
    'password': 'superuser_password',
    'host': 'localhost',
    'port': 5432
}


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
cities_df = cities_df.rename({'City name':'city','Country/territory':'country','Continental region':'continent','Population':'population','Latitude':'latitude','Longitude':'longitude','Elevation (m)':'elevation'})
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
db_conn_uri = f"postgresql://{db_conn_dict['username']}:{db_conn_dict['password']}@{db_conn_dict['host']}:{db_conn_dict['port']}/{db_conn_dict['db_name']}"

capitals_with_coordinates_sdc.write_database(table_name='reference.country_info',connection=db_conn_uri,if_table_exists='replace')

#%%
#create flags table
drop_table_sql = f'''DROP TABLE IF EXISTS reference.flags;'''
create_table_sql = f'''CREATE TABLE reference.flags (country VARCHAR(200), flag TEXT);'''

db_conn_engine = create_engine(f"postgresql+psycopg2://{db_conn_dict['username']}:{db_conn_dict['password']}@{db_conn_dict['host']}:{db_conn_dict['port']}/{db_conn_dict['db_name']}")

with db_conn_engine.connect() as conn:
    try:
        conn = conn.execution_options(isolation_level='READ COMMITTED')
        with conn.begin():
            db_cursor = conn.connection.cursor()
            db_cursor.execute(drop_table_sql)
            db_cursor.execute(create_table_sql)
            conn.commit()
            print('Table created')
    except Exception as e:
        print('Cannot create table:',e)

#%%
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
    with db_conn_engine.connect() as conn:
        conn = conn.execution_options(isolation_level='READ COMMITTED')

        with conn.begin():
            try:
                with open(file,'rb') as f:
                    # get rid of dots and square brackets, create country and flag pair
                    flags_dict = {'country':re.split('[/.\\[\\]]',file)[1],'flag': f.read()}
                    
                insert_data_sql = "INSERT INTO reference.flags (country,flag) VALUES (:c,:f)"
                conn.execute(text(insert_data_sql),{'c': flags_dict['country'],'f': flags_dict['flag']})
                flag_counter += 1
                conn.commit()
            except Exception as e:
                print(f'Could not read {file}:',e)
                conn.rollback()
        print(f'succesfully added {flag_counter} countries')

pl.read_database_uri('SELECT * FROM reference.flags',db_conn_uri)

#%%
# load country mapping
country_mapping = pl.read_csv('country_mapping_utf8.csv')

country_mapping.write_database('reference.country_mapping',connection = db_conn_uri,if_table_exists = 'replace',engine='adbc')

pl.read_database_uri('SELECT * FROM reference.country_mapping',db_conn_uri)


#%%
#TODO conn gets stuck
with db_conn_engine.connect() as conn:
    conn = conn.execution_options(isolation_level='READ COMMITTED')

    try:
        add_column = f'''ALTER TABLE reference.country_info ADD flag_country_reference VARCHAR;'''
        db_cursor = conn.connection.cursor()
        db_cursor.execute(add_column)
   
        join_tables = f'''UPDATE reference.country_info SET flag_country_reference = (SELECT flag_country_reference FROM reference.country_mapping WHERE (country_info.country = country_mapping.wiki_country_reference))'''
        db_cursor.execute(join_tables)
        
        pl.read_database_uri('SELECT * FROM reference.country_info',db_conn_uri)
        join_tables = f'''UPDATE reference.country_info SET flag = (SELECT flag FROM flags WHERE (country_info.country = flags.country))'''
        db_cursor.execute(join_tables)
        print('The country_info table was updated succesfully. The flag mappings have been added.')
        conn.commit()
    except Exception as e:
        conn.rollback()
        print('Had to rollback, could not update country_info table with flags\n',e)

#%%
pl.read_database_uri('SELECT * FROM reference.flags',db_conn_uri)

pl.read_database_uri('SELECT * FROM reference.country_info where flag IS NOT NULL',db_conn_uri)

# %%
conn.close()
# %%
