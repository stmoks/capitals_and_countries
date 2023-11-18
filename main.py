import pandas as pd


url = 'https://en.wikipedia.org/wiki/List_of_countries_whose_capital_is_not_their_largest_city'
list_of_tables = pd.read_html(url)
print(list_of_tables[0])