#%%
import requests
from bs4 import BeautifulSoup
import os
import urllib
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
news_items = soup.find_all('li')
news = []

links = []
for k in news_items:
    m = k.get_text() 
    if 'South Africa' in m:
        news.append(k)   
        links.append(k.find_all('a')[0].get('href'))
       
news
links

#%%
links = ['https://www.wikipedia.com/'] + links

with urllib.request.urlopen() as response:
    html = response.read()
    sub_page = BeautifulSoup(html)
    print(sub_page)
