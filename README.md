# Trails in the Sky FC - Arts Simulator

A build finder tool for *The Legend of Heroes: Trails in the Sky First Chapter*, the remake.

Building an optimal setup in Trails in the Sky FC can be challenging due to many variables, like which quartzes you have available and the restrictions on each character’s orbment lines, especially during mid-chapters, when the availability of quartzes is greater, but you still don't have the best ones. This tool helps you easily find the best quartz combinations to unlock your chosen arts. You can also prioritize quartzes you want to use and maximize the range of arts your character can access.

The tool is still in development, and some characters are still missing, mainly because I couldn't find their ornament restrictions online. I haven't finished the game yet, but I already find the tool useful.

## Quick Start

### Requirements

- Python 3.9 or higher
- pip (Python package manager)

### Installation

1. Clone or download this repository
2. Install dependencies:

```bash
pip install -r requirements.txt
```

### Running the App

```bash
streamlit run app.py
```

The app will automatically open in your default web browser (typically at `http://localhost:8501`).

## How to Use

### 1. Select Your Character

Choose the character you want to build for. Each character has a unique orbment structure with different slot configurations and restrictions.

### 2. Configure Your Search

- **Available Quartz**: Select which quartz you have access to (use "All" to select everything)
- **Prioritized Quartz** (optional): Quartz that will be tried first during the search
- **Filter out builds without ALL prioritized quartzes**: When enabled, only shows builds containing all your prioritized quartz
- **Desired Arts**: Select the arts you want to unlock in your build
- **Max Builds**: Set how many build results you want (default: 50)

### 3. Find Builds

Click **"Find Builds"** to start the search. The algorithm will:
- Find all valid quartz combinations that unlock your desired arts
- Sort results by total arts unlocked (most arts first)
- Cache results for faster repeated searches

### 4. Review Results

Each build shows:
- **Quartz Setup**: Color-coded quartz by element, with arrows showing placement order
- **Line Elements**: Total elemental values for each orbment line
- **Unlocked Arts**: All arts available with this setup (⭐ marks your desired arts)

**Tip**: Hover over any quartz or art name to see detailed information!

## Key Features

### 🎯 Smart Search Algorithm
- Recursive tree-based solver with lexicographic ordering optimization
- Respects all game constraints (families, blade/shield limits, slot restrictions)
- Finds builds efficiently even with large quartz pools
- **⚡ Parallel processing (Experimental)**: Leverages multiple CPU cores for 2-8x faster results

### 💾 Save & Load
- Save multiple configurations for different characters and strategies
- Auto-save option to preserve changes automatically
- Settings persist across app restarts

### 🎨 Color-Coded Display
- Quartz colored by element (Earth=Brown, Water=Blue, Fire=Red, Wind=Green, Time=Purple, Space=Gold, Mirage=Grey)
- Arts grouped and colored by element for easy identification
- Interactive tooltips with detailed information

### ⚡ Performance
- Intelligent caching system stores search results
- Progress tracking shows combinations checked and builds found
- Clear cache option when you need fresh results

## Game Constraints

The simulator automatically enforces all Trails FC orbment rules:

1. **Family Restriction**: No two quartzes of the same family on the same orbment
2. **Blade Limit**: Maximum one Blade-type quartz per line (shared slot exempt)
3. **Shield Limit**: Maximum one Shield-type quartz per line (shared slot exempt)
4. **Slot Restrictions**: Some slots only accept quartz of a specific element
5. **Shared Slots**: The root quartz contributes to all lines

## Tips for Best Results

1. **Start Broad**: Select all available quartz first, then narrow down with prioritized quartz
2. **Prioritize Wisely**: Use prioritized quartz to favor specific setups without over-constraining the search
3. **Filter Required Quartz**: If you must use specific quartz (e.g., limited rare quartz), enable "Filter out builds without ALL prioritized quartzes" to only see builds with those quartz
4. **Check Total Arts**: Builds are sorted by total arts unlocked - sometimes a build unlocks bonus arts you didn't request!
5. **Use Cache**: The cache speeds up repeated searches with the same parameters
6. **Enable Parallel Processing**: For large searches (many quartz/arts), enable parallel processing in settings for significant speedup
7. **Experiment**: Try different desired arts combinations to discover unexpected synergies

## Troubleshooting

**No builds found?**
- Ensure you have enough quartz selected
- Check that your desired arts are compatible (don't require conflicting elements)
- Try increasing the "Max Builds" limit
- Verify you haven't set conflicting prioritized quartz

**App running slowly?**
- Reduce the number of selected quartz to narrow the search space
- Use prioritized quartz to guide the search
- Check the progress counter to see search activity
- Clear cache if it's grown too large

**Results don't match game?**
- Verify your character data matches your game version
- Check that quartz data is complete (especially `quartz_element` property)
- Report any discrepancies with specific build examples

## Data Files

The app uses three JSON data files in the `data/` directory:
- `characters.json`: Orbment structures for each character
- `quartz.json`: All quartz with stats and elements
- `arts.json`: All arts with elemental requirements

## Support

For technical documentation, algorithm details, or to contribute, see `Developer Documentation.md`.

---

**Note**: This is a fan-made tool. All game content and terminology are the property of Nihon Falcom.
