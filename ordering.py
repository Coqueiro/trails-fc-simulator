"""
Lexicographic ordering utilities for the quartz solver.

This module handles the ordering constraints that eliminate redundant permutations
in the search space while maintaining correctness.
"""

from typing import Set, Dict, TYPE_CHECKING

if TYPE_CHECKING:
    from helpers import GameData


class LexicographicOrdering:
    """
    Manages lexicographic ordering constraints for quartz placement.

    The ordering ensures that within linear segments of the orbment tree,
    quartz are placed in sorted order. This eliminates permutations that
    would result in the same elemental values.

    Quartz are sorted by:
    1. Total element count (descending - more elements first)
    2. Name (alphabetically as tiebreaker)

    This optimization is only applied to linear segments where the parent
    node is not shared/branching, preserving independence between branches.
    """

    def __init__(self, game_data: 'GameData'):
        """Initialize the ordering tracker.

        Args:
            game_data: GameData instance for quartz lookups
        """
        self.game_data = game_data
        # Maps line_index -> last_used_quartz_index
        self.last_quartz_index_per_line: Dict[int, int] = {}

    def should_apply_ordering(self, current_node) -> bool:
        """
        Determine if lexicographic ordering should apply for this node.

        Ordering is applied only for linear segments (nodes whose parent
        is not shared/branching). This eliminates redundant permutations
        within each line while preserving independence between branches.

        Args:
            current_node: The slot node being populated

        Returns:
            True if ordering constraints should be applied
        """
        return (current_node.parent is not None and
                not current_node.parent.is_shared())

    def get_sorted_available_quartz(self, available_quartz: Set[str]) -> list:
        """
        Sort available quartz for consistent ordering.

        Sorting priority:
        1. Total element count (descending - more elements first)
        2. Quartz name (alphabetically as tiebreaker)

        Args:
            available_quartz: Set of quartz names available for placement

        Returns:
            Sorted list of quartz names
        """
        def sort_key(quartz_name: str):
            quartz = self.game_data.quartz_map[quartz_name]
            # Count total elements (sum of all element values)
            element_count = sum(quartz.elements.values())
            # Return negative count for descending order, then name for ascending
            return (-element_count, quartz_name)

        return sorted(available_quartz, key=sort_key)

    def get_minimum_index(self, current_node) -> int:
        """
        Get the minimum quartz index allowed for this node based on ordering.

        Args:
            current_node: The slot node being populated

        Returns:
            Minimum index (-1 if no constraint)
        """
        line_idx = current_node.line_index
        return self.last_quartz_index_per_line.get(line_idx, -1)

    def should_skip_quartz(self, current_node, quartz_idx: int) -> bool:
        """
        Check if a quartz should be skipped due to ordering constraints.

        Args:
            current_node: The slot node being populated
            quartz_idx: Index of the quartz in the sorted list

        Returns:
            True if this quartz violates ordering and should be skipped
        """
        if not self.should_apply_ordering(current_node):
            return False

        min_index = self.get_minimum_index(current_node)
        return quartz_idx <= min_index

    def update_last_index(self, current_node, quartz_idx: int):
        """
        Update the last used quartz index for the current line.

        Args:
            current_node: The slot node that was just populated
            quartz_idx: Index of the quartz that was placed
        """
        if self.should_apply_ordering(current_node):
            line_idx = current_node.line_index
            self.last_quartz_index_per_line[line_idx] = quartz_idx

    def copy(self) -> 'LexicographicOrdering':
        """
        Create a copy of this ordering state for branching.

        Returns:
            New LexicographicOrdering instance with copied state
        """
        new_ordering = LexicographicOrdering(self.game_data)
        new_ordering.last_quartz_index_per_line = self.last_quartz_index_per_line.copy()
        return new_ordering
