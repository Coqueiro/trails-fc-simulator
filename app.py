"""
Streamlit Web UI for Trails FC Arts Simulator
"""
import streamlit as st
import json
import os
from pathlib import Path
from datetime import datetime
from solver import BuildFinder
from helpers import GameData


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
SETTINGS_DIR = Path("saved_settings")
SETTINGS_DIR.mkdir(exist_ok=True)

# Cache directory
CACHE_DIR = Path(".cache")
CACHE_DIR.mkdir(exist_ok=True)

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


def get_cache_key(character: str, quartz: list, desired_quartz: list, arts: list, max_builds: int) -> str:
    """Generate a cache key from search parameters."""
    import hashlib
    
    # Create a deterministic string from parameters
    cache_data = {
        'character': character,
        'quartz': sorted(quartz),
        'desired_quartz': sorted(desired_quartz),
        'arts': sorted(arts),
        'max_builds': max_builds
    }
    
    # Generate hash
    cache_str = json.dumps(cache_data, sort_keys=True)
    return hashlib.md5(cache_str.encode()).hexdigest()


def load_cached_results(cache_key: str):
    """Load cached results if available."""
    cache_file = CACHE_DIR / f"{cache_key}.json"
    if cache_file.exists():
        try:
            with open(cache_file, 'r') as f:
                results = json.load(f)
                # Convert unlocked_arts back to sets for consistency
                for build in results:
                    if 'unlocked_arts' in build and isinstance(build['unlocked_arts'], list):
                        build['unlocked_arts'] = set(build['unlocked_arts'])
                return results
        except:
            pass
    return None


def save_cached_results(cache_key: str, results: list):
    """Save results to cache."""
    cache_file = CACHE_DIR / f"{cache_key}.json"
    
    # Convert sets to lists for JSON serialization
    serializable_results = []
    for build in results:
        build_copy = build.copy()
        if 'unlocked_arts' in build_copy and isinstance(build_copy['unlocked_arts'], set):
            build_copy['unlocked_arts'] = sorted(list(build_copy['unlocked_arts']))
        serializable_results.append(build_copy)
    
    with open(cache_file, 'w') as f:
        json.dump(serializable_results, f, indent=2)


# Initialize session state
if 'initialized' not in st.session_state:
    # Load last session if available
    last_session = load_last_session()
    
    if last_session:
        st.session_state.settings_name = last_session.get('last_settings_file', 'default')
        st.session_state.auto_save = last_session.get('auto_save', True)
        
        # Try to load the last settings file
        loaded = load_settings(st.session_state.settings_name)
        if loaded:
            st.session_state.selected_character = loaded.get('character', 'Estelle')
            st.session_state.selected_quartz = loaded.get('selected_quartz', [])
            st.session_state.desired_quartz = loaded.get('desired_quartz', [])
            st.session_state.selected_arts = loaded.get('selected_arts', [])
            st.session_state.max_builds = loaded.get('max_builds', 50)
        else:
            # File doesn't exist, use defaults
            st.session_state.selected_character = "Estelle"
            st.session_state.selected_quartz = []
            st.session_state.desired_quartz = []
            st.session_state.selected_arts = []
            st.session_state.max_builds = 50
    else:
        # No last session, use defaults
        st.session_state.settings_name = "default"
        st.session_state.auto_save = True
        st.session_state.selected_character = "Estelle"
        st.session_state.selected_quartz = []
        st.session_state.desired_quartz = []
        st.session_state.selected_arts = []
        st.session_state.max_builds = 50
    
    st.session_state.initialized = True


def auto_save_if_enabled():
    """Auto-save current settings if enabled."""
    if st.session_state.auto_save:
        settings = {
            'character': st.session_state.selected_character,
            'selected_quartz': st.session_state.selected_quartz,
            'desired_quartz': st.session_state.desired_quartz,
            'selected_arts': st.session_state.selected_arts,
            'max_builds': st.session_state.max_builds
        }
        save_settings(st.session_state.settings_name, settings)
    
    # Always save last session state (which file is open, auto-save preference)
    save_last_session(st.session_state.settings_name, st.session_state.auto_save)


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
                st.session_state.selected_character = loaded.get('character', 'Estelle')
                st.session_state.selected_quartz = loaded.get('selected_quartz', [])
                st.session_state.desired_quartz = loaded.get('desired_quartz', [])
                st.session_state.selected_arts = loaded.get('selected_arts', [])
                st.session_state.max_builds = loaded.get('max_builds', 50)
                
                # Save this as the last session
                save_last_session(st.session_state.settings_name, st.session_state.auto_save)
                
                st.success(f"Loaded: {selected_file}")
                st.rerun()
    
    # Save settings
    new_name = st.text_input("Settings Name", value=st.session_state.settings_name)
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("💾 Save", use_container_width=True):
            st.session_state.settings_name = new_name
            settings = {
                'character': st.session_state.selected_character,
                'selected_quartz': st.session_state.selected_quartz,
                'desired_quartz': st.session_state.desired_quartz,
                'selected_arts': st.session_state.selected_arts,
                'max_builds': st.session_state.max_builds
            }
            save_settings(new_name, settings)
            save_last_session(st.session_state.settings_name, st.session_state.auto_save)
            st.success(f"Saved: {new_name}")
            st.rerun()
    
    with col2:
        new_auto_save = st.checkbox(
            "Auto-save",
            value=st.session_state.auto_save
        )
        if new_auto_save != st.session_state.auto_save:
            st.session_state.auto_save = new_auto_save
            save_last_session(st.session_state.settings_name, st.session_state.auto_save)
    
    st.divider()
    
    # Info
    st.subheader("📊 Current Settings")
    st.write(f"**File:** {st.session_state.settings_name}")
    st.write(f"**Character:** {st.session_state.selected_character}")
    st.write(f"**Quartz:** {len(st.session_state.selected_quartz)}")
    st.write(f"**Required:** {len(st.session_state.desired_quartz)}")
    st.write(f"**Arts:** {len(st.session_state.selected_arts)}")
    
    st.divider()
    
    # Cache info
    st.subheader("🗄️ Cache")
    cache_files = list(CACHE_DIR.glob("*.json"))
    st.write(f"**Cached results:** {len(cache_files)}")
    if st.button("Clear Cache", use_container_width=True):
        for cache_file in cache_files:
            cache_file.unlink()
        st.success("Cache cleared!")
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
        
        # Quartz selection
        st.markdown("**Available Quartz** · [Reference Guide](https://gamefaqs.gamespot.com/ps5/503564-trails-in-the-sky-1st-chapter/faqs/82117/quartz-list)")
        
        col1, col2 = st.columns([4, 1])
        with col1:
            selected_quartz = st.multiselect(
                "Select quartz",
                options=sorted(game_data.quartz_map.keys()),
                default=st.session_state.selected_quartz,
                label_visibility="collapsed",
                key="quartz_selector"
            )
            # Update session state and rerun if changed
            if selected_quartz != st.session_state.selected_quartz:
                st.session_state.selected_quartz = selected_quartz
                auto_save_if_enabled()
                st.rerun()
        
        with col2:
            st.write("")  # Spacing
            if st.button("All", key="select_all_quartz", use_container_width=True):
                st.session_state.selected_quartz = sorted(list(game_data.quartz_map.keys()))
                auto_save_if_enabled()
                st.rerun()
            if st.button("Clear", key="clear_quartz", use_container_width=True):
                st.session_state.selected_quartz = []
                auto_save_if_enabled()
                st.rerun()
        
        st.caption(f"Selected: {len(st.session_state.selected_quartz)} quartz")
        
        # Desired quartz (must have in builds)
        st.markdown("**Required Quartz** (must be in every build)")
        
        col1, col2 = st.columns([4, 1])
        with col1:
            # Only show quartz that are in the available pool
            available_for_desired = [q for q in st.session_state.selected_quartz]
            desired_quartz = st.multiselect(
                "Select required quartz",
                options=sorted(available_for_desired),
                default=[q for q in st.session_state.desired_quartz if q in available_for_desired],
                label_visibility="collapsed",
                key="desired_quartz_selector"
            )
            # Update session state and rerun if changed
            if desired_quartz != st.session_state.desired_quartz:
                st.session_state.desired_quartz = desired_quartz
                auto_save_if_enabled()
                st.rerun()
        
        with col2:
            st.write("")  # Spacing
            if st.button("Clear", key="clear_desired_quartz", use_container_width=True):
                st.session_state.desired_quartz = []
                auto_save_if_enabled()
                st.rerun()
        
        st.caption(f"Required: {len(st.session_state.desired_quartz)} quartz")
        
        # Arts selection
        st.markdown("**Desired Arts** · [Reference Guide](https://gamefaqs.gamespot.com/ps5/503564-trails-in-the-sky-1st-chapter/faqs/82117/arts-list)")
        
        col1, col2 = st.columns([4, 1])
        with col1:
            selected_arts = st.multiselect(
                "Select arts",
                options=sorted(game_data.arts_map.keys()),
                default=st.session_state.selected_arts,
                label_visibility="collapsed",
                key="arts_selector"
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
            # Get character (needed for both cache and search)
            character = game_data.get_character(st.session_state.selected_character)
            
            # Generate cache key
            cache_key = get_cache_key(
                st.session_state.selected_character,
                st.session_state.selected_quartz,
                st.session_state.desired_quartz,
                st.session_state.selected_arts,
                st.session_state.max_builds
            )
            
            # Try to load from cache
            cached_builds = load_cached_results(cache_key)
            
            if cached_builds is not None:
                st.info("✅ Loaded results from cache!")
                builds = cached_builds
            else:
                # Create placeholders for progress updates
                progress_placeholder = st.empty()
                spinner_placeholder = st.empty()
                
                with spinner_placeholder:
                    with st.spinner("Searching for builds..."):
                        quartz_set = set(st.session_state.selected_quartz)
                        
                        finder = BuildFinder(
                            character,
                            quartz_set,
                            st.session_state.selected_arts,
                            game_data,
                            max_builds=st.session_state.max_builds,
                            desired_quartz=set(st.session_state.desired_quartz)
                        )
                        
                        # Create a callback to update progress
                        def progress_callback():
                            progress_placeholder.info(
                                f"🔍 {finder.combinations_checked:,} combinations checked, "
                                f"{len(finder.valid_builds)} valid builds so far..."
                            )
                        
                        finder.progress_callback = progress_callback
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
                                        line_elements = tree.calculate_elements_for_path(paths[line_idx], game_data)
                                        elem_str = ", ".join([f"{e}: {v}" for e, v in sorted(line_elements.items())]) if line_elements else "None"
                                        st.markdown(f"**Line {line_idx + 1}:** `{elem_str}`")
                                
                                # Show quartz in compact format
                                quartz_list = [f"{p['quartz']}" for p in by_line[line_idx]]
                                st.caption(" → ".join(quartz_list))
                        
                        with col2:
                            with st.expander(f"✨ Unlocked Arts ({build['total_arts']})", expanded=True):
                                # Show unlocked arts (all of them, but compact)
                                unlocked = sorted(build['unlocked_arts'])
                                for art in unlocked:
                                    marker = "⭐" if art in st.session_state.selected_arts else "•"
                                    st.caption(f"{marker} {art}")
            else:
                st.error("❌ No valid builds found with the selected quartz and arts.")
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
st.caption(f"Settings: {st.session_state.settings_name} | Auto-save: {'✅' if st.session_state.auto_save else '❌'}")
