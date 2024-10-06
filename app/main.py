#%%
from typing import Union
from fastapi import FastAPI
from pydantic import BaseModel
from pydantic_extra_types.country import CountryAlpha3

# %%
app = FastAPI(
    title='Dumela API'
)

class Country(BaseModel):
    country: CountryAlpha3


@app.get('/')
def get_country_info(country_iso: str):
    country = Country(country = country_iso)
    return country


@app.get('/items/{item_id}')
def read_item(item_id: int = 2, q: Union[str, None] = None):
    return {'item_id': item_id, 'q': q}

# @app.put('/items/{item_id}')
# def update_item(item_id: int, item: Item):
#     return {'item_name': item.is_offer, 'item_id': item_id}