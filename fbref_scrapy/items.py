# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy
from scrapy import Field, Selector
import pandas as pd
from itemloaders.processors import Compose

def extract_table(table: scrapy.Selector) -> pd.DataFrame:
    """Extracts an FBRef table from the provided selector, along with any player
    IDs found. Should work on advanced stats or shots tables.

    Args:
        table (scrapy.Selector): Scrapy selector item added using add_xpath()

    Returns:
        pd.DataFrame: Table converted to dataframe. Not cleaned.
    """
    # Get list of columns
    vars = table.xpath("./thead/tr[last()]/th/@data-stat").getall()

    # Iterate through each row of the table, getting each stat
    # * Needs to be done row by row to account for occasional missing values
    data = []  # Empty list to store data
    for row in table.xpath("./tbody/tr"):
        row_data = {}
        # Get player ID
        row_data["player_id"] = row.xpath('./*[@data-stat = "player"]//@href').get()

        for var in vars:
            text = row.xpath("./*[@data-stat = $var]//text()", var=var).getall()
            # Some cols contain additional strings prefixed
            # Player - whitespace for subs, nationality - two letter code
            row_data[var] = text[-1].strip()  # Keep second item
            # For any "player" stat, we also need to get the ID
            if "player" in var:
                id_col = var + "_id"
                row_data[id_col] = row.xpath(
                    "./*[@data-stat = $var]//@href", var=var
                ).re('(?<=\/players\/)[a-zA-Z0-9]+')
        data.append(row_data)
    # Combine rows into pandas DataFrame
    return pd.DataFrame(data)


class MatchDetailsItem(scrapy.Item):
    # Match Details - Written to Match Results table
    # match_id = Field()  # Single value
    officials = Field()
    team_ids = Field()
    # managers = Field()
    # captains = Field()
    # formations = Field()
    # lineups = Field()

    # Advanced Stats Tables
    # Each combines all the available stats into a single table
    # Will later be split into separate tables in pipeline
    table_stats_home = Field(input_processor=Compose(extract_table))
    table_stats_away = Field(input_processor=Compose(extract_table))

    # Shots Table
    # table_shots = Field(input_processor=MapCompose(extract_table))
