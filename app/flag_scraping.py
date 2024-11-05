#%%
import requests
from bs4 import BeautifulSoup
import os,re


# Define the URL of the Wikipedia page
url = 'https://en.wikipedia.org/wiki/Gallery_of_sovereign_state_flags#T'
# %%


response = requests.get(url)
response.raise_for_status()  # Ensure the request was successful - only produces error if it occurs

# Parse the HTML content using BeautifulSoup
soup = BeautifulSoup(response.content, 'html.parser')

# Find all the image tags that correspond to flags
flag_images = soup.find_all('img')

# Create a directory to save the flag images
os.makedirs('flags', exist_ok=True)

# create base url for images
base_url = 'https:'
#%%
# download flags
for img in flag_images:
    img_url = base_url + img['src']
    img_name = img_url.split('/')[-1]
    match = re.search(r'Flag_of_(.*?)\.svg',img_name)
    country_name = match.group(1) if match else None

    
    try:
        img_response = requests.get(img_url)
        img_response.raise_for_status()  
        
        # Save the image to the 'flags' directory
        with open(os.path.join('flags', f'{country_name}.svg.png'), 'wb') as file:
            file.write(img_response.content)
        print(f'Downloaded {img_name}')
    except:
        print(f'Invalid URL {img_url}')

print(f'All valid flags have been downloaded - {len(flag_images)} flags in total')

# %%
