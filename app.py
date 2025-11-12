"""
Streamlit Web UI for Trails FC Arts Simulator
"""
import streamlit as st
import json
import os
import html
import multiprocessing
from pathlib import Path
from datetime import datetime
from solver import BuildFinder
from helpers import GameData

# Set multiprocessing start method for compatibility (especially macOS)
try:
    multiprocessing.set_start_method('spawn', force=True)
except RuntimeError:
    pass  # Already set

# Page configuration
st.set_page_config(
    page_title="Trails FC Arts Simulator",
    page_icon="🎮",
    layout="wide"
)

# Initialize game data


@st.cache_resource
def load_game_data():
    return GameData()


game_data = load_game_data()

# Settings directory
SETTINGS_DIR = Path(".saved_settings")
SETTINGS_DIR.mkdir(exist_ok=True)

# Cache directory
CACHE_DIR = Path(".cache")
CACHE_DIR.mkdir(exist_ok=True)


def generate_cache_key(character_name, quartz_set, desired_arts, max_builds, prioritized_quartz):
    """Generate a unique cache key for a search configuration."""
    import hashlib

    # Create a deterministic string representation
    config_str = json.dumps({
        "character": character_name,
        "quartz": sorted(list(quartz_set)),
        "arts": sorted(desired_arts),
        "max_builds": max_builds,
        "prioritized_quartz": sorted(list(prioritized_quartz))
    }, sort_keys=True)

    # Generate hash
    return hashlib.md5(config_str.encode()).hexdigest()


def save_cached_results(cache_key, builds):
    """Save build results to cache."""
    cache_file = CACHE_DIR / f"{cache_key}.json"

    # Convert sets to lists for JSON serialization
    serializable_builds = []
    for build in builds:
        serializable_build = build.copy()
        if 'unlocked_arts' in serializable_build:
            serializable_build['unlocked_arts'] = sorted(
                list(serializable_build['unlocked_arts']))
        serializable_builds.append(serializable_build)

    with open(cache_file, 'w') as f:
        json.dump(serializable_builds, f, indent=2)


def load_cached_results(cache_key):
    """Load build results from cache if available."""
    cache_file = CACHE_DIR / f"{cache_key}.json"

    if not cache_file.exists():
        return None

    with open(cache_file, 'r') as f:
        builds = json.load(f)

    # Convert lists back to sets
    for build in builds:
        if 'unlocked_arts' in build:
            build['unlocked_arts'] = set(build['unlocked_arts'])

    return builds


def count_cache_items():
    """Count the number of cached results."""
    if not CACHE_DIR.exists():
        return 0
    return len(list(CACHE_DIR.glob("*.json")))


def clear_cache():
    """Clear all cached results."""
    if not CACHE_DIR.exists():
        return 0

    count = 0
    for cache_file in CACHE_DIR.glob("*.json"):
        cache_file.unlink()
        count += 1
    return count


# Last session file
LAST_SESSION_FILE = SETTINGS_DIR / ".last_session.json"


def save_settings(filename: str, settings: dict):
    """Save settings to a JSON file."""
    filepath = SETTINGS_DIR / f"{filename}.json"
    with open(filepath, 'w') as f:
        json.dump(settings, f, indent=2)
    return filepath


def load_settings(filename: str) -> dict:
    """Load settings from a JSON file."""
    filepath = SETTINGS_DIR / f"{filename}.json"
    if filepath.exists():
        with open(filepath, 'r') as f:
            return json.load(f)
    return None


def save_last_session(settings_name: str, auto_save: bool):
    """Save last session state."""
    session_data = {
        'last_settings_file': settings_name,
        'auto_save': auto_save
    }
    with open(LAST_SESSION_FILE, 'w') as f:
        json.dump(session_data, f, indent=2)


def load_last_session() -> dict:
    """Load last session state."""
    if LAST_SESSION_FILE.exists():
        try:
            with open(LAST_SESSION_FILE, 'r') as f:
                return json.load(f)
        except:
            pass
    return None


def get_saved_settings_list():
    """Get list of saved settings files."""
    if not SETTINGS_DIR.exists():
        return []
    files = [f.stem for f in SETTINGS_DIR.glob("*.json")]
    return sorted(files)


def delete_settings(filename: str):
    """Delete a settings file."""
    filepath = SETTINGS_DIR / f"{filename}.json"
    if filepath.exists():
        filepath.unlink()


# Initialize session state
if 'initialized' not in st.session_state:
    # Load last session if available
    last_session = load_last_session()

    if last_session:
        st.session_state.settings_name = last_session.get(
            'last_settings_file', 'default')
        st.session_state.auto_save = last_session.get('auto_save', True)

        # Try to load the last settings file
        loaded = load_settings(st.session_state.settings_name)
        if loaded:
            st.session_state.selected_character = loaded.get(
                'character', 'Estelle')
            st.session_state.selected_quartz = loaded.get(
                'selected_quartz', [])
            st.session_state.prioritized_quartz = loaded.get(
                'prioritized_quartz', [])
            st.session_state.selected_arts = loaded.get('selected_arts', [])
            st.session_state.max_builds = loaded.get('max_builds', 50)
            st.session_state.use_parallel = loaded.get('use_parallel', False)
        else:
            # File doesn't exist, use defaults
            st.session_state.selected_character = "Estelle"
            st.session_state.selected_quartz = []
            st.session_state.prioritized_quartz = []
            st.session_state.selected_arts = []
            st.session_state.max_builds = 50
            st.session_state.use_parallel = False
    else:
        # No last session, use defaults
        st.session_state.settings_name = "default"
        st.session_state.auto_save = True
        st.session_state.selected_character = "Estelle"
        st.session_state.selected_quartz = []
        st.session_state.prioritized_quartz = []
        st.session_state.selected_arts = []
        st.session_state.max_builds = 50
        st.session_state.use_parallel = False

    st.session_state.initialized = True


def auto_save_if_enabled():
    """Auto-save current settings if enabled."""
    if st.session_state.auto_save:
        settings = {
            'character': st.session_state.selected_character,
            'selected_quartz': st.session_state.selected_quartz,
            'prioritized_quartz': st.session_state.prioritized_quartz,
            'selected_arts': st.session_state.selected_arts,
            'max_builds': st.session_state.max_builds,
            'use_parallel': st.session_state.use_parallel
        }
        save_settings(st.session_state.settings_name, settings)

    # Always save last session state (which file is open, auto-save preference)
    save_last_session(st.session_state.settings_name,
                      st.session_state.auto_save)


# Title
st.title("🎮 Trails in the Sky FC - Arts Simulator")
st.markdown("Find optimal quartz builds for your desired arts")

# Sidebar for settings management
with st.sidebar:
    st.header("⚙️ Settings Management")

    # Settings file management
    st.subheader("Load/Save Settings")

    saved_files = get_saved_settings_list()

    col1, col2 = st.columns([3, 1])
    with col1:
        selected_file = st.selectbox(
            "Settings File",
            options=["<new>"] + saved_files,
            index=0 if st.session_state.settings_name not in saved_files
            else saved_files.index(st.session_state.settings_name) + 1
        )

    with col2:
        st.write("")
        st.write("")
        if selected_file != "<new>" and st.button("🗑️"):
            delete_settings(selected_file)
            st.rerun()

    # Load settings
    if selected_file != "<new>":
        if st.button("📂 Load", use_container_width=True):
            loaded = load_settings(selected_file)
            if loaded:
                # Load settings
                st.session_state.settings_name = selected_file
                st.session_state.selected_character = loaded.get(
                    'character', 'Estelle')
                st.session_state.selected_quartz = loaded.get(
                    'selected_quartz', [])
                st.session_state.prioritized_quartz = loaded.get(
                    'prioritized_quartz', [])
                st.session_state.selected_arts = loaded.get(
                    'selected_arts', [])
                st.session_state.max_builds = loaded.get('max_builds', 50)
                st.session_state.use_parallel = loaded.get('use_parallel', False)

                # Save this as the last session
                save_last_session(st.session_state.settings_name,
                                  st.session_state.auto_save)

                st.success(f"Loaded: {selected_file}")
                st.rerun()

    # Save settings
    new_name = st.text_input(
        "Settings Name", value=st.session_state.settings_name)

    col1, col2 = st.columns(2)
    with col1:
        if st.button("💾 Save", use_container_width=True):
            st.session_state.settings_name = new_name
            settings = {
                'character': st.session_state.selected_character,
                'selected_quartz': st.session_state.selected_quartz,
                'prioritized_quartz': st.session_state.prioritized_quartz,
                'selected_arts': st.session_state.selected_arts,
                'max_builds': st.session_state.max_builds,
                'use_parallel': st.session_state.use_parallel
            }
            save_settings(new_name, settings)
            save_last_session(st.session_state.settings_name,
                              st.session_state.auto_save)
            st.success(f"Saved: {new_name}")
            st.rerun()

    with col2:
        new_auto_save = st.checkbox(
            "Auto-save",
            value=st.session_state.auto_save
        )
        if new_auto_save != st.session_state.auto_save:
            st.session_state.auto_save = new_auto_save
            save_last_session(st.session_state.settings_name,
                              st.session_state.auto_save)

    st.divider()

    # Info
    st.subheader("📊 Current Settings")
    st.write(f"**File:** {st.session_state.settings_name}")
    st.write(f"**Character:** {st.session_state.selected_character}")
    st.write(f"**Quartz:** {len(st.session_state.selected_quartz)}")
    st.write(f"**Prioritized:** {len(st.session_state.prioritized_quartz)}")
    st.write(f"**Arts:** {len(st.session_state.selected_arts)}")

    st.divider()

    # Cache management
    st.subheader("💾 Cache Management")
    cache_count = count_cache_items()
    st.write(f"**Cached searches:** {cache_count}")
    if st.button("🗑️ Clear Cache", use_container_width=True, disabled=(cache_count == 0)):
        cleared = clear_cache()
        st.success(
            f"Cleared {cleared} cached search{'es' if cleared != 1 else ''}!")
        st.rerun()


# Main content
tab1, tab2 = st.tabs(["🎯 Build Finder", "ℹ️ About"])

with tab1:
    st.header("Build Finder")

    # Configuration section (compact)
    with st.expander("⚙️ Configuration", expanded=True):
        # Row 1: Character and Max Builds
        col1, col2 = st.columns(2)
        with col1:
            characters = sorted([char.name for char in game_data.characters])
            selected_char = st.selectbox(
                "Character",
                options=characters,
                index=characters.index(st.session_state.selected_character)
            )
            if selected_char != st.session_state.selected_character:
                st.session_state.selected_character = selected_char
                auto_save_if_enabled()
                st.rerun()

        with col2:
            max_builds = st.slider(
                "Max Builds",
                min_value=10,
                max_value=500,
                value=st.session_state.max_builds,
                step=10
            )
            if max_builds != st.session_state.max_builds:
                st.session_state.max_builds = max_builds
                auto_save_if_enabled()
        
        # Parallel processing option
        use_parallel = st.checkbox(
            "⚡ Use parallel processing (faster on multi-core systems) - Experimental",
            value=st.session_state.use_parallel,
            help="⚠️ Experimental feature. Splits the search across multiple CPU cores for faster results. Recommended for large searches. May have stability issues on some systems."
        )
        if use_parallel != st.session_state.use_parallel:
            st.session_state.use_parallel = use_parallel
            auto_save_if_enabled()

        # Quartz selection
        st.markdown(
            "**Available Quartz** · [Reference Guide](https://gamefaqs.gamespot.com/ps5/503564-trails-in-the-sky-1st-chapter/faqs/82117/quartz-list)")

        col1, col2 = st.columns([4, 1])
        with col1:
            selected_quartz = st.multiselect(
                "Select quartz",
                options=sorted(game_data.quartz_map.keys()),
                default=st.session_state.selected_quartz,
                label_visibility="collapsed"
            )
            # Update session state and rerun if changed
            if selected_quartz != st.session_state.selected_quartz:
                st.session_state.selected_quartz = selected_quartz
                # Remove any prioritized quartz that are no longer selected
                st.session_state.prioritized_quartz = [
                    q for q in st.session_state.prioritized_quartz
                    if q in selected_quartz
                ]
                auto_save_if_enabled()
                st.rerun()

        with col2:
            st.write("")  # Spacing
            if st.button("All", key="select_all_quartz", use_container_width=True):
                st.session_state.selected_quartz = sorted(
                    list(game_data.quartz_map.keys()))
                auto_save_if_enabled()
                st.rerun()
            if st.button("Clear", key="clear_quartz", use_container_width=True):
                st.session_state.selected_quartz = []
                st.session_state.prioritized_quartz = []
                auto_save_if_enabled()
                st.rerun()

        st.caption(f"Selected: {len(st.session_state.selected_quartz)} quartz")

        # Prioritized Quartz selection
        if st.session_state.selected_quartz:
            st.markdown("**Prioritized Quartz** (optional)")
            st.caption("These quartz will be tried first during build search")

            col1, col2 = st.columns([4, 1])
            with col1:
                prioritized_quartz = st.multiselect(
                    "Select prioritized quartz",
                    options=sorted(st.session_state.selected_quartz),
                    default=st.session_state.prioritized_quartz,
                    label_visibility="collapsed"
                )
                # Update session state and rerun if changed
                if prioritized_quartz != st.session_state.prioritized_quartz:
                    st.session_state.prioritized_quartz = prioritized_quartz
                    auto_save_if_enabled()
                    st.rerun()

            with col2:
                st.write("")  # Spacing
                if st.button("Clear", key="clear_prioritized", use_container_width=True):
                    st.session_state.prioritized_quartz = []
                    auto_save_if_enabled()
                    st.rerun()

            st.caption(
                f"Prioritized: {len(st.session_state.prioritized_quartz)} quartz")

        # Arts selection
        st.markdown(
            "**Desired Arts** · [Reference Guide](https://gamefaqs.gamespot.com/ps5/503564-trails-in-the-sky-1st-chapter/faqs/82117/arts-list)")

        col1, col2 = st.columns([4, 1])
        with col1:
            selected_arts = st.multiselect(
                "Select arts",
                options=sorted(game_data.arts_map.keys()),
                default=st.session_state.selected_arts,
                label_visibility="collapsed"
            )
            # Update session state and rerun if changed
            if selected_arts != st.session_state.selected_arts:
                st.session_state.selected_arts = selected_arts
                auto_save_if_enabled()
                st.rerun()

        with col2:
            st.write("")  # Spacing
            if st.button("Clear", key="clear_arts", use_container_width=True):
                st.session_state.selected_arts = []
                auto_save_if_enabled()
                st.rerun()

        st.caption(f"Selected: {len(st.session_state.selected_arts)} arts")

    # Run solver button
    if st.button("🔍 Find Builds", type="primary", use_container_width=True):
        if not st.session_state.selected_arts:
            st.error("Please select at least one desired art!")
        elif not st.session_state.selected_quartz:
            st.error("Please select at least one quartz!")
        else:
            # Generate cache key
            character = game_data.get_character(
                st.session_state.selected_character)
            quartz_set = set(st.session_state.selected_quartz)
            prioritized_set = set(st.session_state.prioritized_quartz)

            cache_key = generate_cache_key(
                st.session_state.selected_character,
                quartz_set,
                st.session_state.selected_arts,
                st.session_state.max_builds,
                prioritized_set
            )

            # Try to load from cache
            builds = load_cached_results(cache_key)

            if builds is not None:
                st.info(f"✅ Loaded {len(builds)} builds from cache!")
            else:
                # Create placeholders for progress updates
                progress_placeholder = st.empty()
                spinner_placeholder = st.empty()

                with spinner_placeholder:
                    with st.spinner("Searching for builds..."):
                        finder = BuildFinder(
                            character,
                            quartz_set,
                            st.session_state.selected_arts,
                            game_data,
                            max_builds=st.session_state.max_builds,
                            prioritized_quartz=prioritized_set
                        )

                        # Create a callback to update progress
                        def progress_callback():
                            progress_placeholder.info(
                                f"🔍 {finder.combinations_checked:,} combinations checked, "
                                f"{len(finder.valid_builds)} valid builds so far..."
                            )

                        finder.progress_callback = progress_callback
                        
                        # Use parallel or single-threaded based on user preference
                        if st.session_state.use_parallel:
                            builds = finder.find_builds_parallel(verbose=False)
                        else:
                            builds = finder.find_builds(verbose=False)

                # Clear progress messages
                progress_placeholder.empty()
                spinner_placeholder.empty()

                # Save to cache
                if builds:
                    save_cached_results(cache_key, builds)

            if builds:
                st.success(f"✅ Found {len(builds)} valid builds!")

                # Display builds
                for i, build in enumerate(builds):
                    with st.expander(
                        f"Build #{i+1} - {build['total_arts']} arts unlocked",
                        expanded=(i == 0)
                    ):
                        # Reconstruct tree to calculate elements per line
                        from tree_structure import OrbmentTree
                        tree = OrbmentTree(character)
                        for placement in build['placements']:
                            for node in tree.all_nodes:
                                if (node.line_index == placement['line_index'] and
                                        node.slot_index == placement['slot_index']):
                                    node.placed_quartz = placement['quartz']
                                    break

                        col1, col2 = st.columns([1, 1])

                        with col1:
                            st.markdown("**🔮 Quartz Setup**")

                            # Inject CSS for quartz tooltips (reuse art-tooltip class)
                            st.markdown("""
                            <style>
                            .quartz-tooltip {
                                position: relative;
                                display: inline-block;
                                cursor: help;
                                margin: 0 4px;
                            }
                            .quartz-tooltip .tooltiptext-quartz {
                                visibility: hidden;
                                width: 250px;
                                background-color: #555;
                                color: #fff;
                                text-align: left;
                                border-radius: 6px;
                                padding: 8px;
                                position: absolute;
                                z-index: 1000;
                                top: 0;
                                left: 100%;
                                margin-left: 10px;
                                opacity: 0;
                                transition: opacity 0.3s;
                                font-size: 0.85em;
                                line-height: 1.4;
                                white-space: pre-wrap;
                            }
                            .quartz-tooltip:hover .tooltiptext-quartz {
                                visibility: visible;
                                opacity: 1;
                            }
                            </style>
                            """, unsafe_allow_html=True)

                            # Define element colors (same as arts)
                            element_colors = {
                                "Earth": "#8B4513",    # Brown
                                "Water": "#1E90FF",    # Blue
                                "Fire": "#FF4500",     # Red-Orange
                                "Wind": "#32CD32",     # Green
                                "Time": "#9370DB",     # Purple
                                "Space": "#FFD700",    # Gold
                                "Mirage": "#969696"    # Grey
                            }

                            # Group by line
                            by_line = {}
                            for placement in build['placements']:
                                line_idx = placement['line_index']
                                if line_idx not in by_line:
                                    by_line[line_idx] = []
                                by_line[line_idx].append(placement)

                            # Get all paths for element calculation
                            paths = tree.get_all_paths()

                            for line_idx in sorted(by_line.keys()):
                                if line_idx == -1:
                                    st.markdown("**Shared:**")
                                else:
                                    # Calculate elements for this line
                                    if line_idx < len(paths):
                                        line_elements = tree.calculate_elements_for_path(
                                            paths[line_idx], game_data)
                                        elem_str = ", ".join([f"{e}: {v}" for e, v in sorted(
                                            line_elements.items())]) if line_elements else "None"
                                        st.markdown(
                                            f"**Line {line_idx + 1}:** `{elem_str}`")

                                # Show quartz with colors and tooltips
                                quartz_html = ""
                                for idx, placement in enumerate(by_line[line_idx]):
                                    quartz_name = placement['quartz']
                                    quartz_data = game_data.quartz_map.get(
                                        quartz_name)

                                    if quartz_data:
                                        # Get color based on quartz_element
                                        color = element_colors.get(
                                            quartz_data.quartz_element, "#888888")

                                        # Create tooltip with description
                                        tooltip = quartz_data.description if quartz_data.description else "No description"

                                        # Add arrow between quartz
                                        if idx > 0:
                                            quartz_html += '<span style="color: #888; margin: 0 4px;">→</span>'

                                        # Add quartz with tooltip
                                        quartz_html += f'<span class="quartz-tooltip" style="color: {color}; font-size: 0.9em;">{quartz_name}<span class="tooltiptext-quartz">{tooltip}</span></span>'
                                    else:
                                        if idx > 0:
                                            quartz_html += ' → '
                                        quartz_html += quartz_name

                                st.markdown(
                                    quartz_html, unsafe_allow_html=True)

                        with col2:
                            st.markdown(
                                f"**✨ Unlocked Arts ({build['total_arts']})**")

                            # Define element colors
                            element_colors = {
                                "Earth": "#8B4513",    # Brown
                                "Water": "#1E90FF",    # Blue
                                "Fire": "#FF4500",     # Red-Orange
                                "Wind": "#32CD32",     # Green
                                "Time": "#9370DB",     # Purple
                                "Space": "#FFD700",    # Gold
                                "Mirage": "#969696"    # Grey
                            }

                            # Group arts by element and sort
                            arts_by_element = {}
                            for art_name in sorted(build['unlocked_arts']):
                                art_data = game_data.arts_map.get(art_name)
                                if art_data:
                                    element = art_data.element
                                    if element not in arts_by_element:
                                        arts_by_element[element] = []
                                    arts_by_element[element].append(art_data)

                            # Display arts with colors and custom CSS tooltips
                            # First, inject the CSS styles
                            st.markdown("""
                            <style>
                            .art-line {
                                display: block;
                                line-height: 1.6;
                            }
                            .art-tooltip {
                                position: relative;
                                display: inline-block;
                                cursor: help;
                            }
                            .art-tooltip .tooltiptext {
                                visibility: hidden;
                                width: 300px;
                                background-color: #555;
                                color: #fff;
                                text-align: left;
                                border-radius: 6px;
                                padding: 8px;
                                position: absolute;
                                z-index: 1000;
                                top: 0;
                                left: 100%;
                                margin-left: 10px;
                                opacity: 0;
                                transition: opacity 0.3s;
                                font-size: 0.85em;
                                line-height: 1.4;
                                white-space: pre-wrap;
                            }
                            .art-tooltip:hover .tooltiptext {
                                visibility: visible;
                                opacity: 1;
                            }
                            </style>
                            """, unsafe_allow_html=True)

                            # Build the HTML content separately
                            html_output = '<div>'
                            for element in ["Earth", "Water", "Fire", "Wind", "Time", "Space", "Mirage"]:
                                if element in arts_by_element:
                                    for art_data in arts_by_element[element]:
                                        marker = "⭐" if art_data.name in st.session_state.selected_arts else "•"
                                        color = element_colors.get(
                                            element, "#888888")

                                        # Create tooltip content
                                        tooltip_content = f"{art_data.effect} | {art_data.range}\n{art_data.description}"

                                        # Wrap in inline tooltip, then in block line
                                        html_output += f'<div class="art-line"><span class="art-tooltip" style="color: {color}; font-size: 0.9em;">{marker} {art_data.name}<span class="tooltiptext">{tooltip_content}</span></span></div>'

                            html_output += '</div>'

                            # Render the HTML
                            st.markdown(html_output, unsafe_allow_html=True)
            else:
                st.error(
                    "❌ No valid builds found with the selected quartz and arts.")
                st.info("Try adding more quartz or adjusting your desired arts.")

with tab2:
    st.header("About")
    st.markdown("""
    ## Trails in the Sky FC - Arts Simulator
    
    This tool helps you find optimal quartz builds for your desired arts in 
    *The Legend of Heroes: Trails in the Sky First Chapter*.
    
    ### Features
    - 🔍 **Smart Search**: Uses recursive tree-based algorithm with lexicographic ordering
    - 💾 **Save/Load**: Save multiple configurations for different characters
    - ⚡ **Auto-save**: Automatically saves your changes
    - 🎯 **Optimized Results**: Builds are sorted by total arts unlocked
    - 📊 **Detailed Analysis**: See elements and unlocked arts for each build
    
    ### How to Use
    1. Go to **Configuration** tab
    2. Select your character
    3. Choose available quartz (or use all)
    4. Select desired arts you want to unlock
    5. Go to **Build Finder** tab and click "Find Builds"
    
    ### Settings Management
    - Use the sidebar to save/load different configurations
    - Enable auto-save for automatic saving
    - Create multiple settings files for different scenarios
    
    ### Algorithm
    The solver uses a recursive tree-based approach with:
    - Lexicographic ordering to eliminate redundant permutations
    - Early stopping once max builds is reached
    - Post-processing to calculate and sort by total arts
    
    ---
    
    **Note**: Builds are found in a specific order, so alphabetically early quartz 
    may appear more frequently in results. Increase max builds for more diversity.
    """)


# Footer
st.divider()
st.caption(
    f"Settings: {st.session_state.settings_name} | Auto-save: {'✅' if st.session_state.auto_save else '❌'}")
