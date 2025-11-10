"""
Simple example showing how to create and use an OrbmentTree.
"""

from helpers import GameData
from tree_structure import OrbmentTree

# Load game data
game_data = GameData()

# Get a character
character = game_data.get_character("Estelle")

# Create tree directly from character
tree = OrbmentTree(character)

# Print the tree structure
print(f"Tree for {character.name}:")
tree.print_tree()

# Get all paths (each path is a complete line)
paths = tree.get_all_paths()
print(f"\nNumber of lines: {len(paths)}")

# Show info about each path
for i, path in enumerate(paths, 1):
    print(f"\nLine {i}: {len(path)} slots")
    for node in path:
        shared_status = " (SHARED)" if node.is_shared() else ""
        restriction = f" - restricted to [{node.restriction}]" if node.restriction else ""
        print(f"  Slot {node.slot_index}{shared_status}{restriction}")

# Example: Place some quartz and calculate elements
print("\n" + "="*60)
print("Example: Placing quartz and calculating elements")
print("="*60)

# Place some quartz in the tree
tree.all_nodes[0].placed_quartz = "EP 2"
tree.all_nodes[1].placed_quartz = "Septium Vein"
tree.all_nodes[2].placed_quartz = "Topaz Shield"

print("\nPlaced quartz:")
for node in tree.all_nodes:
    if node.placed_quartz:
        print(
            f"  Slot {node.slot_index} (Line {node.line_index}): {node.placed_quartz}")

# Calculate total elements
elements = tree.calculate_elements(game_data)
print(f"\nTotal elements: {elements}")

# Reset the tree
tree.reset()
print("\nTree reset - all placements cleared")
