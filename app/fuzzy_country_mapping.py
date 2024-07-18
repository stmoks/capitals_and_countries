import polars as pl
from thefuzz import process,fuzz

flags_df = pl.read_database('SELECT country FROM flags',db_conn)
countries_ref_df = capitals_df.select(['country'])

#TODO create join on join table for flag names
# bring the country name representations together
x = pl.DataFrame(capitals_df['country']).map_rows(lambda x: (process.extractOne(x[0],flags_df['country'],scorer=fuzz.token_set_ratio))[0] + ';' + x[0])

# extract 
x.with_columns(pl.col('map').str.extract(r'.*(;)?',0))