# Save and load settings for this project to config.yml

import sys
from pathlib import Path

from ruamel.yaml import YAML

import helpers


class FbrefConfig:
    def __init__(self, override=None) -> None:
        """Initializes FbrefConfig object and loads file if available.

        Args:
            override (Path, optional): Optional pathlib Path object pointing to
            a different config YAML file. Defaults to None.
        """
        default_file = Path.cwd() / "config.yml"
        self.path = override if override else default_file

        self.yaml = YAML()
        try:
            self.config = self.yaml.load(self.path)
        except FileNotFoundError:
            print("Settings file not found.")
            self.config = {}  # Initialize empty dict

    def save(self) -> None:
        """Saves settings to file"""
        self.yaml.dump(self.config, self.path)

    def update_tables(self, urls: list) -> set:
        """Checks table types at given FBref match URLs and matches with
        priority list in config. Adds any additional table types.

        Args:
            urls (list): List of FBref match URLs

        Returns:
            set: Set of added table types, or None if no changes
        """
        try:
            setting_priorities = self.config["tables"]
        except KeyError:
            setting_priorities = dict()  # Initialize empty dict

        tables = helpers.get_table_types(urls)
        table_types = set(tables.values())

        if setting_priorities:
            # Check if table types match
            if table_types.issubset(set(setting_priorities.keys())):
                return None  # No updates required

        # New settings have been added
        new_settings = setting_priorities  # First add existing
        added = table_types.difference(set(setting_priorities.keys()))

        for table in added:
            if table == "summary":
                new_settings[table] = len(table_types)  # Set to last priority
            elif table == "misc":
                new_settings[table] = len(table_types) - 1  # Set to penultimate
            else:
                new_settings[table] = 1  # Add all others with rank 1 by default

        # Save changes to object
        self.config["tables"] = new_settings

        # Return set of table types added
        return added

    def update_variables(self, urls: list) -> tuple:
        """Update variables from FBRef sample match URLs and map to tables based
        on defined table priorities.

        Args:
            urls (list): List of FBref match URLs

        Returns:
            tuple of (added (dict), removed (dict)):  Returns variables which
            have been added or removed per table.
        """
        try:
            existing_map = self.config["variables"]
        except KeyError:
            existing_map = dict()  # Empty dict

        # Get variables from page(s)
        all_vars = helpers.get_all_variables(urls)
        new_map = helpers.remove_duplicate_values(
            variables=all_vars, ranks=self.config["tables"]
        )

        added = helpers.find_difference(new_map, existing_map)
        removed = helpers.find_difference(existing_map, new_map)

        # Save changes to object if any
        if added or removed:
            self.config["variables"] = new_map

        return (added, removed)


# --------------------------------------------
# Main Function - Run file directly to execute
# --------------------------------------------

if __name__ == "__main__":
    user_file = Path.cwd() / "config.user.yml"  # Overwrite file for gitignore
    if user_file.exists():
        config = FbrefConfig(override=user_file)
    else:
        config = FbrefConfig()  # Default "config.yml" used

    # Get URLs to build list of tables and variables
    print(
        "Provide FBRef match URL to scan for available variables."
        "Variables not in at least one of these pages will be ignored by scraper.\n"
        "A recent match from the Top 5 European Leagues/UEFA Champions League "
        "should contain all the possible variables."
    )
    urls = input("Reference URL(s): ")
    urls = list(map(str.strip, urls.split(",")))

    # Check types of stats tables
    changes = config.update_tables(urls)
    if changes:
        print("New tables added to config: {}".format(changes))

        # Ask before saving changes
        choice = input("Save changes (Y/N)? ")
        if choice in ("Y", "y"):
            print("Saving changes. Update priorities in config.yml and rerun.")
            config.save()  # Save changes
            sys.exit()
        else:
            print("Exiting without saving changes.")
            sys.exit()
    else:
        print("No changes to table priorities.")

    # Check variables within stat tables
    added, removed = config.update_variables(urls)
    if added or removed:
        print("Variables added: {}".format(added))
        print("Variables removed: {}".format(removed))

        # Ask before saving changes
        choice = input("Save changes (Y/N)? ")
        if choice in ("Y", "y"):
            print("Saving changes.")
            config.save()  # Save changes
            sys.exit()  # Exit to allow user to update priorities
        else:
            print("Exiting without saving changes.")
            sys.exit()
