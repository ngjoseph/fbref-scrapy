"""
Contains helper functions to set up the scraper or change configuration.
"""

import copy

import requests
from scrapy.http import TextResponse


def select_top_priority(items: dict, priority: list) -> list:
    """Recursively remove items from a list based on the passed priority order,
    until only a single item remains in the list.

    Args:
        items (list): List of values to narrow down to single value
        priority (list): List of values in order low priority -> high priority

    Returns:
        [list]: List containing a single item
    """

    # Create copies of mutable list arguments
    items_copy = list(items[:])
    priority_copy = list(priority[:])

    if len(items_copy) == 1:
        return items_copy[0]  # Return single item

    for p in priority_copy:
        if p in items_copy:
            # If low priority item found, remove and recursively repeat
            items_copy.remove(p)
            priority_copy.remove(p)
            return select_top_priority(items_copy, priority_copy)


def get_table_types(urls: list) -> dict:
    """Gets a list of tables with their types from FBref page.

    Args:
        urls (list): List of FBref match URLs

    Returns:
        dict: {Table Selector: Type}
        None: if no tables found
    """
    table_types = {} # Empty dict to collect tables from all URLs
    for url in urls:
        res = requests.get(url)
        response = TextResponse(res.url, body=res.text, encoding="utf-8")
        
        ids = response.xpath('//div[@itemprop="performer"]//a/@href').re(
            "(?<=\/squads\/)[a-zA-Z0-9]+"
        )
        all_tables = response.xpath('//table[contains(@id, "stats")]')

        if not all_tables:
            return None  # No tables found

        for table in all_tables:
            # Extract label from table ID
            table_types[table] = (
                table.xpath("@id")
                .get()
                .replace("stats", "")
                .replace(ids[0], "")
                .replace(ids[1], "")
                .strip(" _")
            )
    return table_types


def get_all_variables(urls: list) -> dict:
    """From a list of FBref match URLs, Returns all table categories and a list
    of variables present in each.

    Args:
        urls (list): List of FBref match URLs

    Returns:
        dict: {table categories : variables}
    """

    all_vars = {}  # Empty dict to store variable lists
    tables = get_table_types(urls)
    if not tables:
        raise Exception("No valid stats tables found.")

    for table, cat in tables.items():
        variables = table.xpath("./thead/tr[last()]/th/@data-stat").getall()
        for v in variables:
            try:
                if v not in all_vars[cat]:
                    all_vars[cat].append(v)
            except KeyError:
                all_vars[cat] = [v]
    # Return dict
    return all_vars


def remove_duplicate_values(variables:dict, ranks: dict) -> dict:
    """Removes duplicated values from input dictionary according to the priority
    order provided.

    Args:
        variables (dict): {category: values} where values are repeated across categories
        ranks (dict): {category: rank} where ranks are numeric. Duplicate values
                    are assigned to the key with lowest numeric rank.

    Returns:
        dict: Input dict with duplicate values removed.
    """
    priorities = copy.deepcopy(ranks)
    categories = list(priorities.keys())

    # Create priority ordered list of categories
    priorities = sorted(
        priorities.items(),
        key=lambda x: x[1],
        reverse=True,
    )
    # Keep only labels
    priorities = [x[0] for x in priorities]
    
    if not set(variables.keys()).issubset(priorities):
        raise Exception(
            'Exception: {} have no assigned ranks. Update settings.yml'.format(
                set(priorities).difference(set(variables.keys()))
            )
        )

    # Join all lists into single list
    all_vars = [item for vars in list(variables.values()) for item in vars]

    # Filter unique stats
    unique_vars = set(all_vars)

    # For each unique stat, find which tables it appears in
    var_categories = {}
    for var in unique_vars:
        cat_list = []
        for cat in categories:
            if var in variables[cat]:
                cat_list.append(cat)
        var_categories[var] = cat_list

    var_map = {}  # Create empty dict
    for var, cats in var_categories.items():

        # If present in >70% of tables, assign to summary
        if (
            all_vars.count(var) > len(categories) * 0.7
            and "summary" in var_categories[var]
        ):
            var_map[var] = "summary"

        # Otherwise, begin removing lower priority categories until one remains
        else:
            var_map[var] = select_top_priority(cats, priorities)

    output = {}  # Create final table mapping
    for cat, vars in variables.items():
        for v in vars:
            if var_map[v] == cat:
                try:
                    output[cat].append(v)
                except KeyError:
                    output[cat] = [v]
    # Return final dict
    return output


def find_difference(left: dict, right: dict) -> dict:
    """Accepts two dicts with list values. Check which items are present in left
    but not in right, similar to set difference.

    Args:
        left (dict): Dict with list values
        right (dict): Dict with list values

    Returns:
        dict: Dict with list values. Contains items in left but not in right
    """
    diff = {} # Empty dict to store differences
    for key, values in left.items():
        if key in right.keys():
            right_values = [v for v in right[key]]
            diff[key] = set(values).difference(
                set(right_values)
            )
        else:
            # If key doesn't exist in right, all values are new
            diff[key] = left[key]
    
    diff = {k:v for k,v in diff.items() if len(v) > 0} # Remove empty
    return diff