"""
Tree-based representation of orbment structure.

Each node represents a slot in the orbment:
- Shared slots have multiple children (one per line they contribute to)
- Non-shared slots have one child (next slot in the same line)
- Leaf nodes are the last slots in each line
"""

from typing import Optional, List, Set
from helpers import GameData, Character


class SlotNode:
    """Represents a slot in the orbment tree."""

    def __init__(self, slot_index: int, line_index: int,
                 restriction: Optional[str] = None):
        """
        Initialize a slot node.

        Args:
            slot_index: Position of this slot in its line
            line_index: Which line this slot belongs to
            restriction: Element restriction (e.g., "Fire", "Water")
        """
        self.slot_index = slot_index
        self.line_index = line_index
        self.restriction = restriction

        # Tree structure
        self.children: List['SlotNode'] = []
        self.parent: Optional['SlotNode'] = None

        # Placement tracking
        self.placed_quartz: Optional[str] = None

    def add_child(self, child: 'SlotNode'):
        """Add a child node."""
        self.children.append(child)
        child.parent = self

    def is_leaf(self) -> bool:
        """Check if this is a leaf node."""
        return len(self.children) == 0

    def is_root(self) -> bool:
        """Check if this is the root node."""
        return self.parent is None

    def is_shared(self) -> bool:
        """Check if this is a shared slot (branches to multiple lines)."""
        return len(self.children) > 1

    def can_place_quartz(self, quartz_name: str, game_data: GameData) -> bool:
        """
        Check if a quartz can be placed in this slot.

        Args:
            quartz_name: Name of the quartz to place
            game_data: Game data for quartz lookup

        Returns:
            True if quartz can be placed (respects restriction)
        """
        if not self.restriction:
            return True

        quartz = game_data.quartz_map[quartz_name]
        return quartz.has_element(self.restriction)

    def __repr__(self):
        shared = "SHARED" if self.is_shared() else "normal"
        restriction = f" [{self.restriction}]" if self.restriction else ""
        quartz = f" = {self.placed_quartz}" if self.placed_quartz else ""
        return (f"SlotNode(line={self.line_index}, slot={self.slot_index}, "
                f"{shared}{restriction}{quartz})")


class OrbmentTree:
    """Tree representation of a character's orbment structure."""

    def __init__(self, character: Character):
        """
        Build tree from character data.

        Args:
            character: Character with orbment lines
        """
        self.character = character
        self.root: Optional[SlotNode] = None
        self.all_nodes: List[SlotNode] = []

        self._build_tree()

    def _build_tree(self):
        """Build the tree structure from character's lines."""
        if not self.character.lines:
            return

        # Check if first slot is shared across multiple lines
        first_slot = self.character.lines[0].slots[0]
        has_shared = first_slot.shared if hasattr(
            first_slot, 'shared') else False

        if has_shared and len(self.character.lines) > 1:
            # Create shared root node
            self.root = SlotNode(
                slot_index=0,
                line_index=-1,  # -1 indicates shared across all lines
                restriction=first_slot.restriction
            )
            self.all_nodes.append(self.root)

            # Build each line as a child of the shared root
            for line_idx, line in enumerate(self.character.lines):
                # Skip first slot (it's the shared root)
                if len(line.slots) > 1:
                    line_root = self._build_line_branch(
                        line, line_idx, start_idx=1)
                    if line_root:
                        self.root.add_child(line_root)
        else:
            # No shared slots - each line is a separate tree
            # For now, just build the first line
            # (In full implementation, might want to handle multiple independent lines)
            self.root = self._build_line_branch(
                self.character.lines[0], 0, start_idx=0)

    def _build_line_branch(self, line, line_idx: int, start_idx: int = 0) -> Optional[SlotNode]:
        """
        Build a linear branch for a single line.

        Args:
            line: Line object with slots
            line_idx: Index of this line
            start_idx: Which slot to start from (skip shared if needed)

        Returns:
            Root node of this branch
        """
        if start_idx >= len(line.slots):
            return None

        # Create nodes for each slot in the line
        nodes = []
        for slot_idx in range(start_idx, len(line.slots)):
            slot = line.slots[slot_idx]
            node = SlotNode(
                slot_index=slot_idx,
                line_index=line_idx,
                restriction=slot.restriction
            )
            nodes.append(node)
            self.all_nodes.append(node)

        # Link them in sequence
        for i in range(len(nodes) - 1):
            nodes[i].add_child(nodes[i + 1])

        return nodes[0] if nodes else None

    def get_all_paths(self) -> List[List[SlotNode]]:
        """
        Get all paths from root to leaves (each path = one complete line).

        Returns:
            List of paths, where each path is a list of nodes
        """
        if not self.root:
            return []

        paths = []
        self._traverse_paths(self.root, [], paths)
        return paths

    def _traverse_paths(self, node: SlotNode, current_path: List[SlotNode],
                        all_paths: List[List[SlotNode]]):
        """Recursively traverse tree to collect all root-to-leaf paths."""
        current_path = current_path + [node]

        if node.is_leaf():
            all_paths.append(current_path)
        else:
            for child in node.children:
                self._traverse_paths(child, current_path, all_paths)

    def print_tree(self, node: Optional[SlotNode] = None, indent: int = 0):
        """Print tree structure for visualization."""
        if node is None:
            node = self.root

        if node is None:
            print("Empty tree")
            return

        print("  " * indent + str(node))
        for child in node.children:
            self.print_tree(child, indent + 1)

    def reset(self):
        """Clear all placed quartz from the tree."""
        for node in self.all_nodes:
            node.placed_quartz = None

    def calculate_elements(self, game_data: GameData) -> dict:
        """
        Calculate total elemental values from all placed quartz in the tree.

        Args:
            game_data: Game data for element calculation

        Returns:
            Dictionary mapping element names to total values (same format as helpers.calculate_elements)
        """
        # Collect all placed quartz names
        placed_quartz = {node.placed_quartz for node in self.all_nodes
                         if node.placed_quartz is not None}

        # Use the helper function to calculate elements
        return game_data.element_calc.calculate_elements(placed_quartz)

    def calculate_unlocked_arts(self, game_data: GameData) -> Set[str]:
        """
        Calculate which arts are unlocked by the current tree configuration.

        An art is unlocked if at least one line (path from root to leaf) has
        sufficient elemental values to meet all the art's requirements.

        Args:
            game_data: Game data for art requirements

        Returns:
            Set of art names that are unlocked
        """
        unlocked_arts = set()

        # Get all paths (each path represents one complete line)
        paths = self.get_all_paths()

        for path in paths:
            # Calculate elements for this line
            quartz_in_line = {node.placed_quartz for node in path
                              if node.placed_quartz is not None}

            if not quartz_in_line:
                continue

            line_elements = game_data.element_calc.calculate_elements(
                quartz_in_line)

            # Check which arts this line unlocks
            for art_name, art in game_data.arts_map.items():
                # Check if all requirements are met
                if all(line_elements.get(elem, 0) >= value
                       for elem, value in art.requirements.items()):
                    unlocked_arts.add(art_name)

        return unlocked_arts

    def count_unlocked_arts(self, game_data: GameData) -> int:
        """
        Count how many arts are unlocked by the current tree configuration.

        Args:
            game_data: Game data for art requirements

        Returns:
            Number of unique arts unlocked
        """
        return len(self.calculate_unlocked_arts(game_data))


# Example usage
if __name__ == "__main__":
    from helpers import GameData

    game_data = GameData()

    # Try with different characters
    for char_name in ["Estelle", "Joshua"]:
        print(f"\n{'='*60}")
        print(f"Orbment Tree for {char_name}")
        print(f"{'='*60}")

        character = game_data.get_character(char_name)
        tree = OrbmentTree(character)

        print("\nTree structure:")
        tree.print_tree()

        print(f"\nAll paths (lines):")
        paths = tree.get_all_paths()
        for i, path in enumerate(paths, 1):
            print(f"  Path {i}: {' -> '.join(str(n) for n in path)}")

        print(f"\nTotal slots: {len(tree.all_nodes)}")
        print(
            f"Shared slots: {sum(1 for n in tree.all_nodes if n.is_shared())}")
