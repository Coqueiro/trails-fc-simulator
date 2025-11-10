"""
Trails FC Arts Simulator - Data Classes and Helper Methods
"""
import json
from dataclasses import dataclass
from typing import Dict, List, Optional, Set
from collections import defaultdict


# ============================================================================
# Data Classes
# ============================================================================

@dataclass
class Quartz:
    """Represents a quartz with elemental values"""
    name: str
    family: str
    type: str
    elements: Dict[str, int]
    effects: Optional[str] = None
    description: Optional[str] = None
    quartz_element: Optional[str] = None  # Single element for restriction purposes

    def has_element(self, element: str) -> bool:
        """Check if quartz provides a specific element (for art unlocking)"""
        return element in self.elements and self.elements[element] > 0
    
    def matches_restriction(self, restriction: str) -> bool:
        """Check if quartz matches a slot restriction.
        
        Uses quartz_element if available, otherwise falls back to checking
        if the quartz has the element in its elements dict.
        """
        if self.quartz_element is not None:
            return self.quartz_element == restriction
        # Fallback for quartz without quartz_element defined yet
        return self.has_element(restriction)


@dataclass
class Art:
    """Represents an art with requirements"""
    name: str
    element: str
    requirements: Dict[str, int]
    ep_cost: Optional[int] = None
    effect: Optional[str] = None
    range: Optional[str] = None
    description: Optional[str] = None


@dataclass
class Slot:
    """Represents a single slot in an orbment line"""
    index: int
    restriction: Optional[str]  # Element restriction (e.g., "Time")
    shared: bool  # Whether this slot is shared between lines

    def can_accept(self, quartz: Optional[Quartz]) -> bool:
        """Check if this slot can accept a specific quartz"""
        if quartz is None:
            return True  # Empty slots are always valid
        if self.restriction is None:
            return True  # No restriction
        # Check if quartz has the required element
        return quartz.has_element(self.restriction)


@dataclass
class Line:
    """Represents an orbment line with slots"""
    name: str
    color: str
    slots: List[Slot]

    def num_slots(self) -> int:
        """Total number of slots"""
        return len(self.slots)

    def num_shared_slots(self) -> int:
        """Number of shared slots"""
        return sum(1 for slot in self.slots if slot.shared)

    def num_unique_slots(self) -> int:
        """Number of unique (non-shared) slots"""
        return sum(1 for slot in self.slots if not slot.shared)

    def shared_slot_indices(self) -> List[int]:
        """Get indices of shared slots"""
        return [i for i, slot in enumerate(self.slots) if slot.shared]


@dataclass
class Character:
    """Represents a character with multiple lines"""
    name: str
    description: str
    lines: List[Line]


# ============================================================================
# Element Calculator
# ============================================================================

class ElementCalculator:
    """Handles element calculations for quartz combinations"""

    def __init__(self, quartz_map: Dict[str, Quartz]):
        self.quartz_map = quartz_map

    def calculate_elements(self, quartz_names: Set[str]) -> Dict[str, int]:
        """
        Calculate total elemental values for a set of quartz.

        Args:
            quartz_names: Set of quartz names

        Returns:
            Dictionary mapping element names to total values
        """
        elements = defaultdict(int)
        for name in quartz_names:
            quartz = self.quartz_map[name]
            for elem, value in quartz.elements.items():
                elements[elem] += value
        return dict(elements)

    def get_required_elements(self, arts: List[Art]) -> Dict[str, int]:
        """
        Get the combined required elements for multiple arts.
        Takes the maximum requirement for each element across all arts.

        Args:
            arts: List of arts

        Returns:
            Dictionary mapping element names to maximum required values
        """
        required = defaultdict(int)
        for art in arts:
            for elem, value in art.requirements.items():
                required[elem] = max(required[elem], value)
        return dict(required)


# ============================================================================
# Data Loader
# ============================================================================

class GameData:
    """Loads and provides access to game data"""

    def __init__(self):
        self.quartz_map: Dict[str, Quartz] = {}
        self.arts_map: Dict[str, Art] = {}
        self.characters: List[Character] = []
        self.element_calc: ElementCalculator = None

        self.load_data()

    def load_data(self):
        """Load all game data from JSON files"""
        # Load quartz
        with open('data/quartz.json', 'r') as f:
            quartz_data = json.load(f)
            for q in quartz_data['quartz']:
                quartz = Quartz(**q)
                self.quartz_map[quartz.name] = quartz

        # Load arts
        with open('data/arts.json', 'r') as f:
            arts_data = json.load(f)
            for a in arts_data['arts']:
                art = Art(**a)
                self.arts_map[art.name] = art

        # Load characters
        with open('data/characters.json', 'r') as f:
            char_data = json.load(f)
            for c in char_data['characters']:
                lines = []
                for line_data in c['lines']:
                    slots = [Slot(**slot_data)
                             for slot_data in line_data['slots']]
                    line = Line(
                        name=line_data['name'],
                        color=line_data['color'],
                        slots=slots
                    )
                    lines.append(line)

                character = Character(
                    name=c['name'],
                    description=c['description'],
                    lines=lines
                )
                self.characters.append(character)

        # Initialize element calculator
        self.element_calc = ElementCalculator(self.quartz_map)

    def get_character(self, name: str) -> Optional[Character]:
        """Get character by name"""
        for char in self.characters:
            if char.name == name:
                return char
        return None


# ============================================================================
# Convenience Functions
# ============================================================================

def get_all_quartz_names(game_data: GameData) -> List[str]:
    """Get all quartz names"""
    return list(game_data.quartz_map.keys())


def get_all_art_names(game_data: GameData) -> List[str]:
    """Get all art names"""
    return list(game_data.arts_map.keys())


def get_all_character_names(game_data: GameData) -> List[str]:
    """Get all character names"""
    return [c.name for c in game_data.characters]
