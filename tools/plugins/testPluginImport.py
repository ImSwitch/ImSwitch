import pkg_resources



def list_installed_plugins(entry_point_groups):
    """List all installed plugins under the specified entry point groups.

    Args:
        entry_point_groups (list of str): A list of entry point group names to search for plugins.
    """
    for group in entry_point_groups:
        print(f"Entry point group: '{group}'")
        entry_points = list(pkg_resources.iter_entry_points(group=group))
        if entry_points:
            for entry_point in entry_points:
                print(f"  - Plugin name: {entry_point.name}, Module: {entry_point.module_name}")
        else:
            print("  No plugins found.")
        print()  # Blank line for better readability

# Example usage
entry_point_groups = [
    'imswitch.implugins.detectors',
    'imswitch.implugins.lasers',
    'imswitch.implugins.positioner'
]

list_installed_plugins(entry_point_groups)


def load_plugins_by_category():
    plugins_by_category = {
        'detectors': [],
        'lasers': [],
        'positioner': []
        }
    for category in plugins_by_category.keys():
        for entry_point in pkg_resources.iter_entry_points(f'imswitch.implugins.{category}'):
            plugin_class = entry_point.load()
            plugin = plugin_class()  # Assuming each plugin class has a no-arg constructor
            plugins_by_category[category].append(plugin)
    return plugins_by_category

# Example usage
plugins = load_plugins_by_category()
for category, plugin_list in plugins.items():
    print(f"Category: {category}")
    for plugin in plugin_list:
        print(f" - {plugin}")
plugins["detectors"][0].startAcquisition()
