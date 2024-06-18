#%%
import pandas as pd
import polars as pl



#%%
news_url = 'https://en.wikipedia.org/wiki/Portal:Current_events'
list_of_tables = pd.read_html(news_url)
news_date_history = list_of_tables[3]
reported_countries = list_of_tables[2].iloc[0,0]
# %%



import folium
m = folium.Map(location=[09.0580, 007.4891])
folium.Map(location=[(09.0580, 007.4891),[-09.0580, -007.4891])])