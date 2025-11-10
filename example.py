"""
Example usage of the game data loader and element calculator
"""
from helpers import GameData


def main():
    print("=" * 70)
    print("TRAILS FC ORBMENT BUILD OPTIMIZER - EXAMPLE")
    print("=" * 70)

    # Load all game data
    print("\n📦 Loading game data...")
    game_data = GameData()

    print(f"   ✓ Loaded {len(game_data.quartz_map)} quartz")
    print(f"   ✓ Loaded {len(game_data.arts_map)} arts")
    print(f"   ✓ Loaded {len(game_data.characters)} characters")

    # Example 1: Calculate elements for a quartz combination
    print("\n" + "=" * 70)
    print("EXAMPLE 1: Calculate Elements")
    print("=" * 70)

    quartz_names = {"Mind 2", "Mercy", "EP 2", "Topaz Shield"}
    print(f"\nQuartz: {quartz_names}")

    elements = game_data.element_calc.calculate_elements(quartz_names)
    print(f"\nTotal Elements:")
    for elem, value in sorted(elements.items()):
        print(f"  {elem}: {value}")

    # Example 2: Get required elements for desired arts
    print("\n" + "=" * 70)
    print("EXAMPLE 2: Required Elements for Arts")
    print("=" * 70)

    desired_art_names = ["Titanic Roar", "La Teara", "Thelas"]
    print(f"\nDesired Arts: {desired_art_names}")

    desired_arts = [game_data.arts_map[name] for name in desired_art_names]

    print("\nIndividual Requirements:")
    for art in desired_arts:
        reqs = ", ".join([f"{elem}: {val}" for elem,
                         val in art.requirements.items()])
        print(f"  {art.name}: {reqs}")

    required_elements = game_data.element_calc.get_required_elements(
        desired_arts)
    print(f"\nCombined Required Elements (maximum across all arts):")
    for elem, value in sorted(required_elements.items()):
        print(f"  {elem}: {value}")

    # Example 3: Character orbment structure
    print("\n" + "=" * 70)
    print("EXAMPLE 3: Character Orbment Structure")
    print("=" * 70)

    estelle = game_data.get_character("Estelle")
    print(f"\n{estelle.name}:")
    print(f"  {estelle.description}")

    for line in estelle.lines:
        print(f"\n  {line.name} ({line.color}):")
        print(f"    Total slots: {line.num_slots()}")
        print(f"    Shared slots: {line.num_shared_slots()}")
        print(f"    Unique slots: {line.num_unique_slots()}")

        for slot in line.slots:
            shared_str = "SHARED" if slot.shared else "unique"
            restriction = f", restricted to {slot.restriction}" if slot.restriction else ""
            print(f"      Slot {slot.index}: {shared_str}{restriction}")

    # Example 4: Validate a known working build
    print("\n" + "=" * 70)
    print("EXAMPLE 4: Validate Known Working Build")
    print("=" * 70)

    line1_quartz = {"EP 2", "Septium Vein", "EP Cut 2", "Topaz Shield"}
    line2_quartz = {"EP 2", "Heal", "Sapphire Shield"}  # EP 2 is shared

    print(f"\nLine 1: {line1_quartz}")
    line1_elements = game_data.element_calc.calculate_elements(line1_quartz)
    print(f"Elements: {line1_elements}")

    print(f"\nLine 2: {line2_quartz}")
    line2_elements = game_data.element_calc.calculate_elements(line2_quartz)
    print(f"Elements: {line2_elements}")

    print("\nChecking which desired arts are satisfied:")
    for art_name in desired_art_names:
        art = game_data.arts_map[art_name]

        # Check if Line 1 satisfies
        line1_satisfies = all(
            line1_elements.get(elem, 0) >= val
            for elem, val in art.requirements.items()
        )

        # Check if Line 2 satisfies
        line2_satisfies = all(
            line2_elements.get(elem, 0) >= val
            for elem, val in art.requirements.items()
        )

        if line1_satisfies:
            print(f"  ✅ {art_name} (satisfied by Line 1)")
        elif line2_satisfies:
            print(f"  ✅ {art_name} (satisfied by Line 2)")
        else:
            print(f"  ❌ {art_name} (NOT satisfied)")

    print("\n" + "=" * 70)
    print("✅ EXAMPLES COMPLETE")
    print("=" * 70)
    print("\nYou can now implement your own solver algorithm!")
    print("See README.md for the full problem description.")


if __name__ == "__main__":
    main()
