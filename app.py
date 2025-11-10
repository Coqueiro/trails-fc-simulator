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
        st.session_state.settings_name = last_session.get('last_settings_file', 'default')
        st.session_state.auto_save = last_session.get('auto_save', True)
        
        # Try to load the last settings file
        loaded = load_settings(st.session_state.settings_name)
        if loaded:
            st.session_state.selected_character = loaded.get('character', 'Estelle')
            st.session_state.selected_quartz = loaded.get('selected_quartz', [])
            st.session_state.selected_arts = loaded.get('selected_arts', [])
            st.session_state.max_builds = loaded.get('max_builds', 50)
        else:
            # File doesn't exist, use defaults
            st.session_state.selected_character = "Estelle"
            st.session_state.selected_quartz = []
            st.session_state.selected_arts = []
            st.session_state.max_builds = 50
    else:
        # No last session, use defaults
        st.session_state.settings_name = "default"
        st.session_state.auto_save = True
        st.session_state.selected_character = "Estelle"
        st.session_state.selected_quartz = []
        st.session_state.selected_arts = []
        st.session_state.max_builds = 50
    
    st.session_state.initialized = True


def auto_save_if_enabled():
    """Auto-save current settings if enabled."""
    if st.session_state.auto_save:
        settings = {
            'character': st.session_state.selected_character,
            'selected_quartz': st.session_state.selected_quartz,
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
    st.write(f"**Arts:** {len(st.session_state.selected_arts)}")


# Main content
tab1, tab2, tab3 = st.tabs(["🎯 Build Finder", "📋 Configuration", "ℹ️ About"])

with tab1:
    st.header("Build Finder")
    
    # Quick stats
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Character", st.session_state.selected_character)
    with col2:
        st.metric("Selected Quartz", len(st.session_state.selected_quartz))
    with col3:
        st.metric("Desired Arts", len(st.session_state.selected_arts))
    with col4:
        st.metric("Max Builds", st.session_state.max_builds)
    
    # Run solver button
    if st.button("🔍 Find Builds", type="primary", use_container_width=True):
        if not st.session_state.selected_arts:
            st.error("Please select at least one desired art!")
        elif not st.session_state.selected_quartz:
            st.error("Please select at least one quartz!")
        else:
            with st.spinner("Searching for builds..."):
                character = game_data.get_character(st.session_state.selected_character)
                quartz_set = set(st.session_state.selected_quartz)
                
                finder = BuildFinder(
                    character,
                    quartz_set,
                    st.session_state.selected_arts,
                    game_data,
                    max_builds=st.session_state.max_builds
                )
                
                builds = finder.find_builds(verbose=False)
                
                if builds:
                    st.success(f"✅ Found {len(builds)} valid builds!")
                    
                    # Display builds
                    for i, build in enumerate(builds):
                        with st.expander(
                            f"Build #{i+1} - {build['total_arts']} arts unlocked",
                            expanded=(i == 0)
                        ):
                            col1, col2 = st.columns([2, 1])
                            
                            with col1:
                                st.subheader("Quartz Placement")
                                
                                # Group by line
                                by_line = {}
                                for placement in build['placements']:
                                    line_idx = placement['line_index']
                                    if line_idx not in by_line:
                                        by_line[line_idx] = []
                                    by_line[line_idx].append(placement)
                                
                                for line_idx in sorted(by_line.keys()):
                                    if line_idx == -1:
                                        st.markdown("**Shared Slot:**")
                                    else:
                                        st.markdown(f"**Line {line_idx + 1}:**")
                                    
                                    for placement in by_line[line_idx]:
                                        st.write(f"  • Slot {placement['slot_index']}: {placement['quartz']}")
                            
                            with col2:
                                st.subheader("Elements")
                                for elem, value in sorted(build['elements'].items()):
                                    st.write(f"**{elem}:** {value}")
                                
                                st.divider()
                                
                                st.subheader("Unlocked Arts")
                                st.write(f"**Total:** {build['total_arts']}")
                                
                                # Show first 15 arts
                                unlocked = sorted(build['unlocked_arts'])
                                for art in unlocked[:15]:
                                    marker = "⭐" if art in st.session_state.selected_arts else "•"
                                    st.write(f"{marker} {art}")
                                
                                if len(unlocked) > 15:
                                    st.write(f"*... and {len(unlocked) - 15} more*")
                else:
                    st.error("❌ No valid builds found with the selected quartz and arts.")
                    st.info("Try adding more quartz or adjusting your desired arts.")

with tab2:
    st.header("Configuration")
    
    # Character selection
    st.subheader("1. Select Character")
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
    
    # Max builds
    st.subheader("2. Max Builds to Find")
    max_builds = st.slider(
        "Maximum number of builds",
        min_value=10,
        max_value=500,
        value=st.session_state.max_builds,
        step=10
    )
    if max_builds != st.session_state.max_builds:
        st.session_state.max_builds = max_builds
        auto_save_if_enabled()
    
    st.divider()
    
    # Quartz selection
    st.subheader("3. Select Available Quartz")
    st.markdown("📚 [Quartz Reference Guide](https://gamefaqs.gamespot.com/ps5/503564-trails-in-the-sky-1st-chapter/faqs/82117/quartz-list)")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        if st.button("Select All Quartz"):
            st.session_state.selected_quartz = sorted(list(game_data.quartz_map.keys()))
            auto_save_if_enabled()
            st.rerun()
    with col2:
        if st.button("Clear Quartz"):
            st.session_state.selected_quartz = []
            auto_save_if_enabled()
            st.rerun()
    
    # Single multiselect for all quartz
    all_quartz = sorted(game_data.quartz_map.keys())
    
    selected_quartz = st.multiselect(
        "Select available quartz",
        options=all_quartz,
        default=st.session_state.selected_quartz,
        help="Choose which quartz are available for builds"
    )
    
    # Display counter after multiselect
    st.write(f"**Selected: {len(selected_quartz)} quartz**")
    
    # Update session state
    if selected_quartz != st.session_state.selected_quartz:
        st.session_state.selected_quartz = selected_quartz
        auto_save_if_enabled()
    
    st.divider()
    
    # Arts selection
    st.subheader("4. Select Desired Arts")
    st.markdown("📚 [Arts Reference Guide](https://gamefaqs.gamespot.com/ps5/503564-trails-in-the-sky-1st-chapter/faqs/82117/arts-list)")
    
    if st.button("Clear Arts"):
        st.session_state.selected_arts = []
        auto_save_if_enabled()
        st.rerun()
    
    # Search for arts
    search_term = st.text_input("🔍 Search arts", "")
    
    # Filter and display arts
    all_arts = sorted(game_data.arts_map.keys())
    filtered_arts = [art for art in all_arts if search_term.lower() in art.lower()] if search_term else all_arts
    
    # Use multiselect for arts
    selected_arts = st.multiselect(
        "Select desired arts",
        options=all_arts,
        default=st.session_state.selected_arts,
        help="Choose the arts you want to unlock"
    )
    
    # Display counter after multiselect
    st.write(f"**Selected: {len(selected_arts)} arts**")
    
    # Update session state
    if selected_arts != st.session_state.selected_arts:
        st.session_state.selected_arts = selected_arts
        auto_save_if_enabled()

with tab3:
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
