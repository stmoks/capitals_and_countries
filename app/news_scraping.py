#%%
import requests
from bs4 import BeautifulSoup
import os
import re

# Define the URL of the Wikipedia page
url = 'https://en.wikipedia.org/wiki/Portal:Current_events'
# %%
response = requests.get(url)

#%%
response.raise_for_status()  # Ensure the request was successful - only produces error if it occurs

# Parse the HTML content using BeautifulSoup
soup = BeautifulSoup(response.content, 'html.parser')

#%%
text = soup.getText()
print(True) if 'South African' in text else print('Nope')

news_items = soup.find_all('ul')
news_items

# %%
