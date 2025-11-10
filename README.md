# Trails in the Sky FC - Orbment Build Optimization Problem

## Problem Statement

Given a character's orbment configuration, a set of available quartz, and desired arts (spells), find all valid quartz configurations that unlock those arts while respecting game constraints.

This is a **Constraint Satisfaction Problem (CSP)** with complex interdependencies between slots, elements, and game rules.

---

## Game Mechanics

### Orbment Structure

Each character has an **orbment** consisting of:
- Two **lines** (sequences of slots)
- Each line has multiple **slots** where quartz can be placed
- Slots can be:
  - **Shared**: The same physical slot counted in both lines
  - **Unique**: Only counted in one line
  - **Restricted**: Only accepts quartz with specific element(s)

### Example: Estelle's Orbment

```
Line 1 (4 slots): [Slot 0*] [Slot 1] [Slot 2] [Slot 3]
Line 2 (3 slots): [Slot 0*] [Slot 1] [Slot 2]
                   
* Slot 0 is SHARED between both lines
```

### Quartz

Each quartz has:
- **Name**: e.g., "Mind 2", "EP 2", "Topaz Shield"
- **Family**: e.g., "Mind", "EP", "Topaz Shield"
- **Type**: "Normal", "Blade", or "Shield"
- **Elements**: Dictionary of element values, e.g., `{"Water": 2}`
- **Effects**: Stat bonuses (not relevant for this problem)

Example:
```json
{
  "name": "Mind 2",
  "family": "Mind",
  "type": "Normal",
  "elements": {"Water": 2}
}
```

### Arts (Spells)

Each art has:
- **Name**: e.g., "Diamond Dust"
- **Requirements**: Element values needed on a **single line**, e.g., `{"Water": 5, "Space": 5}`

An art is unlocked if **either line** has sufficient element values.

Example:
```json
{
  "name": "Diamond Dust",
  "element": "Water",
  "requirements": {"Water": 5, "Space": 5}
}
```

### Element Calculation

Elements are summed **per line**:

```
Line 1: ["Mind 2", "Mercy", "EP 2", "Topaz Shield"]
  Mind 2:        Water: 2
  Mercy:         Water: 3, Earth: 3
  EP 2:          Space: 1
  Topaz Shield:  Earth: 3
  ─────────────────────────────────
  TOTAL:         Water: 5, Earth: 6, Space: 1
```

---

## Constraints

### 1. **Slot Restrictions**
Some slots only accept quartz with specific elements.

Example (Joshua):
- Slot 0 (shared): Only accepts quartz with "Time" element
- Line 1, Slot 3: Only accepts quartz with "Time" element

**Rule**: If a slot has a restriction, the placed quartz MUST have that element.

### 2. **Shared Slots**
Certain slots are physically the same between lines.

**Rule**: Quartz in a shared slot contributes its elements to BOTH lines.

Example:
```
Line 1: [EP 2] [Mind 2] [Mercy] [Topaz Shield]
Line 2: [EP 2] [Heal] [Sapphire Shield]
         ^
         Same "EP 2" quartz - counts for both lines
```

### 3. **Quartz Uniqueness**
Each quartz can only be used **once** (except when in a shared slot).

**Rule**: 
- A quartz in Line 1's unique slot CANNOT appear in Line 2's unique slot
- A quartz in a shared slot appears in BOTH lines (it's the same physical slot)

### 4. **Family Conflicts**
No two quartz from the same family can be in the same line.

**Rule**: Within a single line, all quartz must have unique families.

Example (INVALID):
```
Line 1: ["Mind 1", "Mind 2", "EP 2"]  ❌ Two "Mind" family quartz
```

### 5. **Blade Type Conflicts**
At most **one** Blade-type quartz per line.

**Rule**: A line cannot contain more than one quartz with `type == "Blade"`.

Example (INVALID):
```
Line 1: ["Poison Blade", "Petrification Blade", "EP 2"]  ❌ Two Blade quartz
```

### 6. **Shield Type Conflicts**
At most **one** Shield-type quartz per line.

**Rule**: A line cannot contain more than one quartz with `type == "Shield"`.

Example (INVALID):
```
Line 1: ["Topaz Shield", "Sapphire Shield", "EP 2"]  ❌ Two Shield quartz
```

### 7. **Empty Slots Allowed**
Slots can be left empty.

**Rule**: Not all slots need to be filled. This increases solution space.

---

## Input

1. **Character**: Name of the character (determines orbment structure)
2. **Available Quartz**: List of quartz names the player owns
3. **Desired Arts**: List of art names the player wants to unlock

## Output

A list of **valid configurations**, where each configuration specifies:
- Quartz placed in each slot of Line 1 (or `None` for empty)
- Quartz placed in each slot of Line 2 (or `None` for empty)
- Total elements for Line 1
- Total elements for Line 2
- All arts unlocked by this configuration

---

## Algorithm Complexity

### Search Space

For Estelle with 26 available quartz:

**Line 1** (4 slots):
- Slot 0: 26 choices + 1 (empty) = 27 options
- Slot 1: 25 choices + 1 = 26 options (if Slot 0 filled)
- Slot 2: 24 choices + 1 = 25 options
- Slot 3: 23 choices + 1 = 24 options
- Naive upper bound: 27 × 26 × 25 × 24 = ~421,200

**Line 2** (3 slots):
- Slot 0: SHARED with Line 1 (no new choices)
- Slot 1: Remaining quartz + empty
- Slot 2: Remaining quartz + empty
- Combined with Line 1: Millions to billions of combinations

**Constraints reduce the space** significantly, but exhaustive search is still expensive.

### Challenge

The problem is challenging because:
1. **Interdependencies**: Shared slots couple the two lines
2. **Multiple constraints**: Each must be checked for every partial solution
3. **Combinatorial explosion**: Even modest numbers of quartz create huge search spaces
4. **Order matters**: For shared slots, which quartz goes in Slot 0 affects both lines

---

## Data Format

### Characters (`data/characters.json`)

```json
{
  "characters": [
    {
      "name": "Estelle",
      "description": "...",
      "lines": [
        {
          "name": "Line 1",
          "color": "blue",
          "slots": [
            {"index": 0, "restriction": null, "shared": true},
            {"index": 1, "restriction": null, "shared": false},
            {"index": 2, "restriction": null, "shared": false},
            {"index": 3, "restriction": null, "shared": false}
          ]
        },
        {
          "name": "Line 2",
          "color": "orange",
          "slots": [
            {"index": 0, "restriction": null, "shared": true},
            {"index": 1, "restriction": null, "shared": false},
            {"index": 2, "restriction": null, "shared": false}
          ]
        }
      ]
    }
  ]
}
```

### Quartz (`data/quartz.json`)

```json
[
  {
    "name": "Mind 2",
    "family": "Mind",
    "type": "Normal",
    "elements": {"Water": 2},
    "effects": "ATS+10%",
    "description": "+2 Water, ATS+10%"
  },
  {
    "name": "Topaz Shield",
    "family": "Topaz Shield",
    "type": "Shield",
    "elements": {"Earth": 3},
    "effects": "Physical Defense +10",
    "description": "+3 Earth, Physical Defense +10"
  }
]
```

### Arts (`data/arts.json`)

```json
[
  {
    "name": "Diamond Dust",
    "element": "Water",
    "requirements": {"Water": 5, "Space": 5},
    "ep_cost": 300,
    "effect": "Arts (S+)",
    "range": "Target - Circle (M)",
    "description": "Water damage to medium circle, Freeze (40%)"
  },
  {
    "name": "Titanic Roar",
    "element": "Earth",
    "requirements": {"Earth": 5, "Wind": 2},
    "ep_cost": 50,
    "effect": "Arts (A+)",
    "range": "All Enemies",
    "description": "Earth damage to all enemies"
  }
]
```

---

## Helper Methods Provided

### `ElementCalculator`

```python
element_calc = ElementCalculator(quartz_map)

# Calculate total elements for a line
elements = element_calc.calculate_elements(["Mind 2", "Mercy", "EP 2"])
# Returns: {'Water': 5, 'Earth': 3, 'Space': 1}

# Get required elements for arts (max across all arts)
required = element_calc.get_required_elements([art1, art2, art3])
# Returns: {'Earth': 5, 'Water': 4, 'Wind': 2, 'Space': 3}
```

### Data Loading

```python
from helpers import GameData

game_data = GameData()

# Access all data
quartz_map = game_data.quartz_map        # Dict[str, Quartz]
arts_map = game_data.arts_map            # Dict[str, Art]
characters = game_data.characters        # List[Character]
element_calc = game_data.element_calc    # ElementCalculator

# Get a character
estelle = game_data.get_character("Estelle")
```

---

## Example Problem Instance

### Input
```
Character: Estelle
Available Quartz: [
  "EP 2", "Septium Vein", "EP Cut 2", "Topaz Shield",
  "Heal", "Sapphire Shield", "Mind 2", "HP 2", ...
]
Desired Arts: ["Titanic Roar", "La Teara", "Thelas"]
```

### Required Elements (calculated from desired arts)
```
{
  "Earth": 5,  # max(Titanic Roar: 5, La Teara: 0, Thelas: 0)
  "Wind": 2,   # max(Titanic Roar: 2, La Teara: 0, Thelas: 0)
  "Water": 4,  # max(Titanic Roar: 0, La Teara: 4, Thelas: 4)
  "Space": 3   # max(Titanic Roar: 0, La Teara: 3, Thelas: 3)
}
```

### Valid Solution Example
```
Line 1: ["EP 2", "Septium Vein", "EP Cut 2", "Topaz Shield"]
  EP 2:          Space: 1
  Septium Vein:  Earth: 3, Wind: 3
  EP Cut 2:      Time: 1, Mirage: 3, Space: 1
  Topaz Shield:  Earth: 3
  ──────────────────────────────────────
  TOTAL:         Earth: 6, Wind: 3, Space: 2, Time: 1, Mirage: 3
  
  ✓ Satisfies: Titanic Roar (needs Earth: 5, Wind: 2)

Line 2: ["EP 2", "Heal", "Sapphire Shield"]
  EP 2:             Space: 1  (shared)
  Heal:             Water: 4
  Sapphire Shield:  Water: 3, Space: 2
  ──────────────────────────────────────
  TOTAL:            Water: 7, Space: 3
  
  ✓ Satisfies: La Teara (needs Water: 4, Space: 3)
  ✓ Satisfies: Thelas (needs Water: 4, Space: 3)

Result: All 3 desired arts unlocked! ✅
```

---

## Constraint Validation Checklist

For each candidate configuration, verify:

- [ ] **Slot restrictions**: Restricted slots only contain compatible quartz
- [ ] **Shared slots**: Same quartz in both lines' shared slot positions
- [ ] **Quartz uniqueness**: No quartz used twice (except shared slots)
- [ ] **Family conflicts**: No duplicate families within a line
- [ ] **Blade conflicts**: At most 1 Blade per line
- [ ] **Shield conflicts**: At most 1 Shield per line
- [ ] **Art requirements**: All desired arts unlocked by at least one line

---

## Suggested Approaches

### 1. Recursive Backtracking
Build configurations slot-by-slot, backtracking when constraints are violated.

**Pros**: Explores search space systematically, can prune early
**Cons**: May need optimizations for large search spaces

### 2. Constraint Propagation
Reduce search space by eliminating invalid choices before search.

**Pros**: Can dramatically reduce combinations to try
**Cons**: More complex to implement

### 3. Greedy Heuristics
Prioritize quartz that provide needed elements or satisfy multiple constraints.

**Pros**: Can find good solutions quickly
**Cons**: May miss optimal solutions

### 4. Hybrid
Combine approaches: use heuristics to guide backtracking, apply constraint propagation.

**Pros**: Balance between speed and completeness
**Cons**: Most complex implementation

---

## Testing

Load the data and test element calculations:

```bash
python3 example.py
```

Or use the helper classes directly:

```python
from helpers import GameData

# Load all game data
game_data = GameData()

print(f"Loaded {len(game_data.quartz_map)} quartz")
print(f"Loaded {len(game_data.arts_map)} arts")
print(f"Loaded {len(game_data.characters)} characters")

# Test element calculation
quartz_names = ["Mind 2", "Mercy", "EP 2"]
elements = game_data.element_calc.calculate_elements(quartz_names)
print(f"Elements: {elements}")

# Test required elements
arts = [
    game_data.arts_map["Titanic Roar"],
    game_data.arts_map["La Teara"],
    game_data.arts_map["Thelas"]
]
required = game_data.element_calc.get_required_elements(arts)
print(f"Required: {required}")
```

---

## Project Structure

```
trails-fc-simulator/
├── data/
│   ├── quartz.json          # 138 quartz definitions
│   ├── arts.json            # All arts with requirements
│   └── characters.json      # Character orbment structures
├── helpers.py               # Data classes and element calculator
├── example.py               # Example usage and validation
├── user_settings.json       # Your saved configuration
├── README.md                # This file
└── .gitignore
```

---

## Summary

This is a **constraint satisfaction problem** where you must:

1. **Place quartz** in orbment slots (or leave empty)
2. **Respect all game constraints** (uniqueness, families, types, restrictions, shared slots)
3. **Achieve element thresholds** to unlock desired arts
4. **Handle shared slots** that affect both lines simultaneously

The challenge lies in the **combinatorial search space** and **interdependent constraints**. An effective solution requires careful algorithm design to balance completeness, correctness, and performance.

Good luck! 🎮✨
