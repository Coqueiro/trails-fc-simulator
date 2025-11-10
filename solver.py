"""
Load settings from user_settings.json
"""
import json
from helpers import GameData


def main():
    # Load user settings
    with open('user_settings.json', 'r') as f:
        settings = json.load(f)

    # Extract settings
    character_name = settings['character']
    available_quartz = settings['selected_quartz']
    desired_arts = settings['selected_arts']

    # Load game data
    game_data = GameData()

    # Get character
    character = game_data.get_character(character_name)

    # Get desired art objects
    desired_art_objs = [game_data.arts_map[name] for name in desired_arts]

    # Calculate required elements
    required_elements = game_data.element_calc.get_required_elements(
        desired_art_objs)

    # Example: Calculate elements from two quartz
    example_quartz = {available_quartz[0], available_quartz[1]}
    example_elements = game_data.element_calc.calculate_elements(
        example_quartz)

    # Filter relevant quartz (those with needed elements)
    relevant_quartz = [
        q_name for q_name in available_quartz
        if any(elem in game_data.quartz_map[q_name].elements
               for elem in required_elements.keys())
    ]

    # Print loaded data
    print(f"Character: {character_name}")
    print(f"Available quartz: {len(available_quartz)}")
    print(f"Desired arts: {desired_arts}")
    print(f"Required elements: {required_elements}")
    print(f"Relevant quartz: {len(relevant_quartz)}")
    print(f"\nExample: Elements from {example_quartz}: {example_elements}")

    # Create test quartz set with known relevant quartz + 3 others
    known_relevant = {"EP 2", "Septium Vein", "EP Cut 2",
                      "Topaz Shield", "Heal", "Sapphire Shield"}
    additional_quartz = {"Mind 1", "Attack 1",
                         "Defense 1"}  # 3 not in user's list
    quartz_set = known_relevant | additional_quartz

    print(f"\nTest quartz set: {quartz_set}")

    # Build finder class
    class BuildFinder:
        """Class to find valid quartz builds through exhaustive search."""

        def __init__(self, character, quartz_pool, desired_arts, game_data):
            self.character = character
            self.quartz_pool = quartz_pool
            self.desired_arts = desired_arts
            self.game_data = game_data

            desired_art_objs = [game_data.arts_map[name]
                                for name in desired_arts]

            required_elements = game_data.element_calc.get_required_elements(
                desired_art_objs)

            self.relevant_quartz = {
                q_name for q_name in quartz_pool
                if any(elem in game_data.quartz_map[q_name].elements
                       for elem in required_elements.keys())
            }

            self._print_info()

        def _print_info(self):
            """Print configuration information."""
            print(f"\n{'='*50}")
            print(f"BUILD FINDER INITIALIZED")
            print(f"{'='*50}")

            print(f"Available quartz: {len(self.quartz_pool)}")
            print(f"Relevant quartz: {len(self.relevant_quartz)}")
            print(f"Required elements: {required_elements}")

            # Create finder and search for builds
    finder = BuildFinder(character, quartz_set, desired_arts, game_data)


if __name__ == "__main__":
    main()
