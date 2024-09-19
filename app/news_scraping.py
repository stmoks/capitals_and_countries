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
topics_text = soup.find_all('p')
topics = []
for p in topics_text:
    topics.append(p.text.strip())
topics = list(set(topics))
topics


# %%
# soup_text = soup.getText()
# news_items = soup.find_all('li')
news_items = soup.find_all('li',lambda tx: 'March' in tx  )
news_items
