import pandas as pd
url = 'https://en.wikipedia.org/wiki/List_of_cities_by_elevation'
new = pd.read_html(url)
print(new)