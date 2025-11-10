"""
Example using actual user settings from user_settings.json
to find builds for Titanic Roar, La Teara, and Thelas.
"""
import json
from solver import BuildFinder
from helpers import GameData


def main():
    print("="*60)
    print("TITANIC ROAR BUILD FINDER")
    print("="*60)

    # Load user settings
    with open('user_settings.json', 'r') as f:
        settings = json.load(f)

    # Extract settings
    character_name = settings['character']
    available_quartz = set(settings['selected_quartz'])
    desired_arts = settings['selected_arts']

    print(f"\nCharacter: {character_name}")
    print(f"Available quartz: {len(available_quartz)}")
    print(f"Desired arts: {desired_arts}")

    # Load game data
    game_data = GameData()
    character = game_data.get_character(character_name)

    # Show required elements
    desired_art_objs = [game_data.arts_map[name] for name in desired_arts]
    required_elements = game_data.element_calc.get_required_elements(
        desired_art_objs)
    print(f"\nRequired elements: {required_elements}")

    # Create finder and search for builds
    print("\n" + "="*60)
    finder = BuildFinder(character, available_quartz, desired_arts, game_data)

    print(
        f"Relevant quartz (with needed elements): {len(finder.relevant_quartz)}")
    print(f"Quartz pool being used: {finder.relevant_quartz}")

    # Find builds
    builds = finder.find_builds(verbose=True)

    # Display results
    print("\n" + "="*60)
    print("RESULTS")
    print("="*60)

    if builds:
        print(f"\n✓ SUCCESS! Found {len(builds)} valid build(s)")
        print(f"Builds are sorted by total unlocked arts (best first)")

        # Show first few builds
        num_to_show = min(5, len(builds))
        for i in range(num_to_show):
            build = builds[i]
            print(f"\n{'='*60}")
            print(f"Build #{i+1} - Unlocks {build['total_arts']} arts total")
            print(f"{'='*60}")
            print(f"Elements: {build['elements']}")

            # Show unlocked arts (first 10)
            unlocked = sorted(build['unlocked_arts'])
            print(f"\nUnlocked arts ({len(unlocked)} total):")
            for j, art in enumerate(unlocked[:10]):
                desired_marker = " ⭐" if art in desired_arts else ""
                print(f"  - {art}{desired_marker}")
            if len(unlocked) > 10:
                print(f"  ... and {len(unlocked) - 10} more")

            print("\nPlacements:")

            # Group by line for better readability
            by_line = {}
            for placement in build['placements']:
                line_idx = placement['line_index']
                if line_idx not in by_line:
                    by_line[line_idx] = []
                by_line[line_idx].append(placement)

            # Display by line
            for line_idx in sorted(by_line.keys()):
                if line_idx == -1:
                    print("  Shared slot:")
                else:
                    print(f"  Line {line_idx + 1}:")

                for placement in by_line[line_idx]:
                    shared_marker = " (SHARED)" if placement['is_shared'] else ""
                    print(
                        f"    Slot {placement['slot_index']}: {placement['quartz']}{shared_marker}")

        if len(builds) > num_to_show:
            print(f"\n{'='*60}")
            print(f"... and {len(builds) - num_to_show} more build(s)")
            print(
                f"Range of total arts: {builds[-1]['total_arts']} to {builds[0]['total_arts']}")
    else:
        print("\n✗ No valid builds found with the available quartz.")
        print("\nPossible reasons:")
        print("- Not enough quartz with required elements")
        print("- Restrictions prevent valid combinations")
        print("- Family/Blade/Shield constraints eliminate all possibilities")

        # Show what's needed vs what's available
        print(f"\nRequired elements: {required_elements}")
        print(f"Available relevant quartz: {len(finder.relevant_quartz)}")


if __name__ == "__main__":
    main()
