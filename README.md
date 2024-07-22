## Capitals and countries

I like to think geography creates a good mental map for thinking about history and lanugage. Those are the two things I'm currently interested in so I created an interactive map that teaches you about a country and it's history as you scroll through.

## Capitals and countries

I like to think geography creates a good mental map for thinking about history and lanugage. Those are the two things I'm currently interested in so I created an interactive map that teaches you about a country and it's history as you scroll through.

By scraping data from Wikipedia links, I put together a table containing the capitals of the world along with basic information about them such as the country, continent, population, and coordinates associated with them.

At the bottom of the script, I use SQL Lite to answer some basic questions about the data. The questions I answer include the following:

1. Which countries have more than 1 capital city?
2. What are the most populous capital cities?
3. Which capital cities have the highest elevation?

### Additional Notes

- Different datasets might contain the same information, but have different encodings or data types. This is often the case when dealing with data that could be in varying languages. In this dataset, this was partly due to the differences in endonyms and exonyms. Other times, it was simply because some sites tables consider all the necessary special characters while other skip some or all.
