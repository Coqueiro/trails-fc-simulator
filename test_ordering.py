#!/usr/bin/env python3.9
"""Test the new element-count-based ordering."""

import sys
import os
os.chdir('/Users/lucas.garcia/Github/trails-fc-simulator')

from helpers import GameData
from ordering import LexicographicOrdering

game_data = GameData()

# Create some test quartz
test_quartz = {
    "Action 2",      # Time: 2 (1 element, sum=2)
    "Cast 2",        # Time: 2, Mirage: 2, Space: 1 (3 elements, sum=5)
    "EP Cut 2",      # Space: 2, Time: 2, Mirage: 1 (3 elements, sum=5)
    "Attack 2",      # Fire: 2 (1 element, sum=2)
    "Mind 2",        # Water: 2 (1 element, sum=2)
}

print("=== Testing New Ordering ===\n")

# Create ordering instance
ordering = LexicographicOrdering(game_data)

# Sort the quartz
sorted_quartz = ordering.get_sorted_available_quartz(test_quartz)

print("Sorted order (by element count, then name):\n")
for i, qname in enumerate(sorted_quartz):
    quartz = game_data.quartz_map[qname]
    element_count = len(quartz.elements)
    element_sum = sum(quartz.elements.values())
    elements_str = ", ".join(f"{k}:{v}" for k, v in quartz.elements.items())
    print(f"{i+1}. {qname:20} - {element_count} elements (sum={element_sum}): {elements_str}")

print("\n" + "="*60)
print("\nExpected order:")
print("1. Cast 2 (3 elements, sum=5)")
print("2. EP Cut 2 (3 elements, sum=5, comes after Cast 2 alphabetically)")
print("3. Action 2 (1 element, sum=2)")
print("4. Attack 2 (1 element, sum=2, comes after Action 2 alphabetically)")
print("5. Mind 2 (1 element, sum=2)")
