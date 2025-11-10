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

            # Calculate properties
            self.num_lines = len(character.lines)

            # Store line sizes for all lines
            self.line_sizes = [line.num_slots() for line in character.lines]

            # Calculate shared slots (from first line, if any)
            self.shared_count = character.lines[0].num_shared_slots(
            ) if self.num_lines > 0 else 0

            # Get shared slot restriction (assuming first slot of first line is shared if any)
            if self.shared_count > 0:
                shared_slot = character.lines[0].slots[0]
                self.shared_restriction = shared_slot.restriction
            else:
                self.shared_restriction = None

            # Calculate relevant quartz (those with needed elements)
            desired_art_objs = [game_data.arts_map[name]
                                for name in desired_arts]
            required_elements = game_data.element_calc.get_required_elements(
                desired_art_objs)
            self.relevant_quartz = {
                q_name for q_name in quartz_pool
                if any(elem in game_data.quartz_map[q_name].elements
                       for elem in required_elements.keys())
            }

            # Calculate valid quartz for each line's restricted slots
            self.line_restricted_quartz = [
                self._get_valid_quartz_for_line(line)
                for line in character.lines
            ]

            self._print_info()

        def _get_valid_quartz_for_line(self, line):
            """Get set of quartz from relevant_quartz valid for any restricted slot in line."""
            restrictions = {
                slot.restriction for slot in line.slots if slot.restriction}

            if not restrictions:
                # No restrictions, all relevant quartz are valid
                return self.relevant_quartz

            # Get quartz that satisfy at least one restriction
            valid = set()
            for q_name in self.relevant_quartz:
                quartz = self.game_data.quartz_map[q_name]
                if any(quartz.has_element(restriction) for restriction in restrictions):
                    valid.add(q_name)

            return valid

        def _print_info(self):
            """Print configuration information."""
            print(f"\n{'='*50}")
            print(f"BUILD FINDER INITIALIZED")
            print(f"{'='*50}")
            print(f"Number of lines: {self.num_lines}")

            # Print info for each line
            for i, (size, restricted) in enumerate(zip(self.line_sizes, self.line_restricted_quartz), 1):
                print(f"Line {i} size: {size}")
                print(f"Line {i} valid for restrictions: {len(restricted)}")

            print(f"Shared count: {self.shared_count}")
            print(f"Shared restriction: {self.shared_restriction}")
            print(f"Available quartz: {len(self.quartz_pool)}")
            print(f"Relevant quartz: {len(self.relevant_quartz)}")

        def get_remaining_quartz_list_after_shared_quartz(self):
            """Generate all possible configurations and validate each."""
            remaining_quartz_list = []

            if self.shared_count > 0:
                # Step 1: Select quartz for shared slot
                for shared_quartz in self.relevant_quartz:
                    # Check if quartz respects shared slot restriction
                    if self.shared_restriction:
                        quartz_obj = self.game_data.quartz_map[shared_quartz]
                        if not quartz_obj.has_element(self.shared_restriction):
                            continue  # Skip if doesn't have required element

                    # This quartz goes in shared slot
                    print(f"\nTrying shared slot: {shared_quartz}")

                    # Remove shared quartz from available pool for remaining slots
                    remaining_quartz_list.append(
                        {"shared_quartz": shared_quartz, "remaining_quartz_list": self.relevant_quartz - {shared_quartz}})
            else:
                remaining_quartz_list.append(
                    {"shared_quartz": None, "remaining_quartz_list": [self.relevant_quartz]})

            return remaining_quartz_list

        def get_remaining_quartz_list_after_restricted_quartz(self, quartz_list):
            pass

            # Create finder and search for builds
    finder = BuildFinder(character, quartz_set, desired_arts, game_data)
    builds = finder.get_remaining_quartz_list_after_shared_quartz()
    print(f"\nBuilds found: {len(builds)}")


if __name__ == "__main__":
    main()
