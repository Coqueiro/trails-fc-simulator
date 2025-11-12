"""
Recursive tree-based solver for finding valid quartz builds.
"""
import json
import multiprocessing
from typing import Set, List, Dict, Tuple
from helpers import GameData, Character
from tree_structure import OrbmentTree, SlotNode
from ordering import LexicographicOrdering


# Global worker function for multiprocessing (must be at module level for pickling)
def _worker_search_subtree(args: Tuple) -> List[Dict]:
    """
    Worker function for parallel processing.
    Explores a subtree starting with a specific first quartz.
    
    Args:
        args: Tuple of (first_quartz_name, first_quartz_idx, character, 
               quartz_pool, desired_arts, game_data, max_builds, prioritized_quartz, 
               filter_without_all_prioritized)
    
    Returns:
        List of valid builds found in this subtree
    """
    (first_quartz, first_idx, character, quartz_pool, desired_arts, 
     game_data, max_builds_per_worker, prioritized_quartz, filter_without_all_prioritized) = args
    
    # Create a BuildFinder instance for this worker
    finder = BuildFinder(character, quartz_pool, desired_arts, game_data, 
                        max_builds_per_worker, prioritized_quartz, filter_without_all_prioritized)
    
    # Create tree
    tree = OrbmentTree(character)
    first_node = tree.all_nodes[0]
    
    # Place the first quartz
    first_node.placed_quartz = first_quartz
    
    # Calculate remaining quartz after first placement
    line_placements = {}
    remaining = finder._calculate_remaining_quartz(
        first_quartz, quartz_pool, first_node, line_placements)
    
    # Create ordering and update for first placement
    ordering = LexicographicOrdering(prioritized_quartz)
    ordering.update_last_index(first_node, first_idx)
    
    # Recursively explore the rest of the tree
    finder._populate_tree_recursive(tree, 1, remaining, line_placements, ordering)
    
    return finder.valid_builds


class BuildFinder:
    """
    Class to find valid quartz builds through recursive tree population.

    Uses lexicographic ordering optimization to eliminate redundant builds:
    - Quartz within each line are placed in sorted order
    - Ordering is NOT applied to shared/branching nodes (preserves independence between branches)
    - Reduces search space from permutations to combinations within each line
    """

    def __init__(self, character: Character, quartz_pool: Set[str],
                 desired_arts: List[str], game_data: GameData, max_builds: int = 50,
                 prioritized_quartz: Set[str] = None, filter_without_all_prioritized: bool = False):
        self.character = character
        self.quartz_pool = quartz_pool
        self.desired_arts = desired_arts
        self.game_data = game_data
        self.max_builds = max_builds
        self.prioritized_quartz = prioritized_quartz if prioritized_quartz is not None else set()
        self.filter_without_all_prioritized = filter_without_all_prioritized

        # Calculate required elements
        desired_art_objs = [game_data.arts_map[name]
                            for name in desired_arts]
        self.required_elements = game_data.element_calc.get_required_elements(
            desired_art_objs)

        # Use all quartz from the pool (user has already pre-filtered)
        self.relevant_quartz = quartz_pool

        # Results storage
        self.valid_builds = []

        # Progress tracking
        self.combinations_checked = 0
        self.progress_callback = None

    def _print_info(self):
        """Print configuration information."""
        print(f"\n{'='*50}")
        print(f"BUILD FINDER INITIALIZED")
        print(f"{'='*50}")
        print(f"Available quartz: {len(self.quartz_pool)}")
        print(f"Relevant quartz: {len(self.relevant_quartz)}")
        print(f"Required elements: {self.required_elements}")
        print(f"Max builds to find: {self.max_builds}")

    def _calculate_remaining_quartz(self, used_quartz: str, available: Set[str],
                                    current_node: SlotNode, line_placements: Dict) -> Set[str]:
        """
        Calculate remaining quartz after placing one.

        Args:
            used_quartz: The quartz just placed
            available: Currently available quartz set
            current_node: The node where quartz was placed
            line_placements: Dict tracking blade/shield placements per line {line_idx: {'blade': set(), 'shield': set()}}

        Returns:
            Set of quartz still available for next placement
        """
        # Start with available minus the used one
        remaining = available - {used_quartz}

        # Get the quartz object
        quartz_obj = self.game_data.quartz_map[used_quartz]

        # Remove all quartz from the same family
        quartz_family = quartz_obj.family
        remaining = {q for q in remaining
                     if self.game_data.quartz_map[q].family != quartz_family}

        # Handle blade/shield restrictions per line
        # If node is shared (root), blade/shield don't count toward line restrictions
        if not current_node.is_shared():
            line_idx = current_node.line_index

            # Track what types have been placed on this line
            if line_idx not in line_placements:
                line_placements[line_idx] = {
                    'blade': set(), 'shield': set()}

            quartz_type = quartz_obj.type

            if quartz_type == 'Blade':
                # Already placed a blade on this line, remove all blades
                if line_placements[line_idx]['blade']:
                    remaining = {q for q in remaining
                                 if self.game_data.quartz_map[q].type != 'Blade'}
                line_placements[line_idx]['blade'].add(used_quartz)

            elif quartz_type == 'Shield':
                # Already placed a shield on this line, remove all shields
                if line_placements[line_idx]['shield']:
                    remaining = {q for q in remaining
                                 if self.game_data.quartz_map[q].type != 'Shield'}
                line_placements[line_idx]['shield'].add(used_quartz)

        return remaining

    def _populate_tree_recursive(self, tree: OrbmentTree, node_index: int,
                                 available_quartz: Set[str], line_placements: Dict,
                                 ordering: LexicographicOrdering) -> None:
        """
        Recursively populate the tree with quartz.

        Args:
            tree: The orbment tree to populate
            node_index: Index of current node in tree.all_nodes
            available_quartz: Set of quartz available for this placement
            line_placements: Dict tracking blade/shield placements per line
            ordering: LexicographicOrdering instance tracking ordering constraints
        """
        # Early exit if we've found enough builds
        if len(self.valid_builds) >= self.max_builds:
            return

        # Base case: all nodes filled
        if node_index >= len(tree.all_nodes):
            # Tree is complete, increment combinations checked
            self.combinations_checked += 1

            # Check if it meets requirements
            # Check if all desired arts are unlocked by any line
            unlocked_arts = tree.calculate_unlocked_arts(self.game_data)

            # Build is valid if all desired arts are unlocked
            if all(art in unlocked_arts for art in self.desired_arts):
                # If filter is enabled, also check if all prioritized quartz are present
                if self.filter_without_all_prioritized and self.prioritized_quartz:
                    used_quartz = {node.placed_quartz for node in tree.all_nodes}
                    if not self.prioritized_quartz.issubset(used_quartz):
                        # Filter out this build - doesn't have all prioritized quartz
                        if self.progress_callback and self.combinations_checked % 100 == 0:
                            self.progress_callback()
                        return
                
                # Valid build! Store a complete copy
                # Store as list of (line_index, slot_index, quartz_name) tuples
                build_copy = {
                    'placements': [
                        {
                            'line_index': node.line_index,
                            'slot_index': node.slot_index,
                            'quartz': node.placed_quartz,
                            'is_shared': node.is_shared()
                        }
                        for node in tree.all_nodes
                    ],
                    'total_arts': 0  # Will be calculated after search
                }
                self.valid_builds.append(build_copy)
                # print(f"  ✓ Found valid build #{len(self.valid_builds)}")

            # Call progress callback if provided (after checking this combination)
            if self.progress_callback and self.combinations_checked % 100 == 0:
                self.progress_callback()
            return

        # Get current node
        current_node = tree.all_nodes[node_index]

        # Sort available quartz for consistent ordering
        sorted_quartz = ordering.get_sorted_available_quartz(available_quartz)

        # Try placing each available quartz that respects restrictions
        for quartz_idx, quartz_name in enumerate(sorted_quartz):
            # Skip if violates lexicographic ordering
            if ordering.should_skip_quartz(current_node, quartz_idx):
                continue

            if current_node.can_place_quartz(quartz_name, self.game_data):
                # Place the quartz
                current_node.placed_quartz = quartz_name

                # Calculate remaining quartz for next placement
                # Make a copy of line_placements for this branch
                line_placements_copy = {
                    line: {'blade': types['blade'].copy(
                    ), 'shield': types['shield'].copy()}
                    for line, types in line_placements.items()
                }

                remaining = self._calculate_remaining_quartz(
                    quartz_name, available_quartz, current_node, line_placements_copy)

                # Copy and update ordering state for this branch
                ordering_copy = ordering.copy()
                ordering_copy.update_last_index(current_node, quartz_idx)

                # Recurse to next node
                self._populate_tree_recursive(tree, node_index + 1,
                                              remaining, line_placements_copy,
                                              ordering_copy)

                # Backtrack - clear this placement for next iteration
                current_node.placed_quartz = None

    def find_builds(self, verbose: bool = True) -> List[Dict]:
        """
        Find all valid builds using recursive tree population.

        Searches until max_builds is reached, then calculates total unlocked arts
        for each build and sorts by total arts (descending).

        Args:
            verbose: Whether to print progress information

        Returns:
            List of valid builds sorted by total arts (descending), each build is a dict with:
            - 'placements': List of quartz placements
            - 'elements': Total elements achieved
            - 'total_arts': Number of arts unlocked
            - 'unlocked_arts': Set of art names unlocked
        """
        if verbose:
            print(
                f"\nStarting recursive search (max {self.max_builds} builds)...")

        # Create the tree structure for this character
        tree = OrbmentTree(self.character)

        if verbose:
            print(f"Tree has {len(tree.all_nodes)} slots to fill")
            print(
                f"Searching with {len(self.relevant_quartz)} relevant quartz")

        # Start recursive population from the first node
        # Initialize with fresh ordering tracker
        self._populate_tree_recursive(
            tree, 0, self.relevant_quartz, {}, LexicographicOrdering(self.prioritized_quartz))

        if verbose:
            print(f"\n{'='*50}")
            print(
                f"Search complete! Found {len(self.valid_builds)} valid builds")
            print("Calculating unlocked arts for each build...")
            print(f"{'='*50}")

        # Calculate total arts for each build
        for build in self.valid_builds:
            # Reconstruct the tree with this build's placements
            tree.reset()
            for placement in build['placements']:
                # Find the node and place the quartz
                for node in tree.all_nodes:
                    if (node.line_index == placement['line_index'] and
                            node.slot_index == placement['slot_index']):
                        node.placed_quartz = placement['quartz']
                        break

            # Calculate unlocked arts
            unlocked_arts = tree.calculate_unlocked_arts(self.game_data)
            build['total_arts'] = len(unlocked_arts)
            build['unlocked_arts'] = unlocked_arts

        # Sort by total arts (descending) - builds with more arts first
        self.valid_builds.sort(key=lambda b: b['total_arts'], reverse=True)

        if verbose and self.valid_builds:
            print(
                f"Best build unlocks {self.valid_builds[0]['total_arts']} arts")

        return self.valid_builds

    def find_builds_parallel(self, verbose: bool = True, num_workers: int = None) -> List[Dict]:
        """
        Find all valid builds using parallel processing across multiple CPU cores.
        
        Splits the search space by first quartz placement - each worker explores
        all builds starting with a different first quartz.
        
        Args:
            verbose: Whether to print progress information
            num_workers: Number of parallel workers (defaults to CPU count - 1)
        
        Returns:
            List of valid builds sorted by total arts (descending)
        """
        # Determine number of workers
        if num_workers is None:
            num_workers = max(1, multiprocessing.cpu_count() - 1)
        
        if verbose:
            print(f"\n{'='*50}")
            print(f"PARALLEL BUILD FINDER")
            print(f"{'='*50}")
            print(f"Using {num_workers} CPU cores")
            print(f"Max builds to find: {self.max_builds}")
        
        # Create the tree structure to analyze first node
        tree = OrbmentTree(self.character)
        first_node = tree.all_nodes[0]
        
        if verbose:
            print(f"Tree has {len(tree.all_nodes)} slots to fill")
            print(f"Searching with {len(self.relevant_quartz)} relevant quartz")
        
        # Get sorted quartz and find valid first choices
        ordering = LexicographicOrdering(self.prioritized_quartz)
        sorted_quartz = ordering.get_sorted_available_quartz(self.relevant_quartz)
        
        # Build list of valid first placements
        valid_first_choices = []
        for idx, quartz_name in enumerate(sorted_quartz):
            if first_node.can_place_quartz(quartz_name, self.game_data):
                valid_first_choices.append((quartz_name, idx))
        
        if verbose:
            print(f"Found {len(valid_first_choices)} valid first quartz choices")
            print(f"Splitting work across {num_workers} workers...\n")
        
        # If very few choices, fall back to single-threaded
        if len(valid_first_choices) < 2:
            if verbose:
                print("Too few branches for parallel processing, using single-threaded mode.")
            return self.find_builds(verbose=verbose)
        
        # Calculate max builds per worker
        # Give each worker a fair share, with some extra to ensure we hit max_builds
        max_builds_per_worker = self.max_builds * 2 // len(valid_first_choices) + 10
        
        # Prepare worker arguments
        worker_args = [
            (quartz_name, idx, self.character, self.quartz_pool, 
             self.desired_arts, self.game_data, max_builds_per_worker, 
             self.prioritized_quartz, self.filter_without_all_prioritized)
            for quartz_name, idx in valid_first_choices
        ]
        
        # Run parallel search
        try:
            with multiprocessing.Pool(num_workers) as pool:
                results = pool.map(_worker_search_subtree, worker_args)
        except Exception as e:
            if verbose:
                print(f"Parallel processing failed: {e}")
                print("Falling back to single-threaded mode.")
            return self.find_builds(verbose=verbose)
        
        # Combine results from all workers
        for worker_builds in results:
            self.valid_builds.extend(worker_builds)
            # Early exit if we have enough builds
            if len(self.valid_builds) >= self.max_builds:
                break
        
        # Trim to max_builds
        if len(self.valid_builds) > self.max_builds:
            self.valid_builds = self.valid_builds[:self.max_builds]
        
        if verbose:
            print(f"\n{'='*50}")
            print(f"Parallel search complete! Found {len(self.valid_builds)} valid builds")
            print("Calculating unlocked arts for each build...")
            print(f"{'='*50}")
        
        # Calculate total arts for each build (reuse tree instance)
        tree.reset()
        for build in self.valid_builds:
            # Reconstruct the tree with this build's placements
            tree.reset()
            for placement in build['placements']:
                # Find the node and place the quartz
                for node in tree.all_nodes:
                    if (node.line_index == placement['line_index'] and
                            node.slot_index == placement['slot_index']):
                        node.placed_quartz = placement['quartz']
                        break
            
            # Calculate unlocked arts
            unlocked_arts = tree.calculate_unlocked_arts(self.game_data)
            build['total_arts'] = len(unlocked_arts)
            build['unlocked_arts'] = unlocked_arts
        
        # Sort by total arts (descending) - builds with more arts first
        self.valid_builds.sort(key=lambda b: b['total_arts'], reverse=True)
        
        if verbose and self.valid_builds:
            print(f"Best build unlocks {self.valid_builds[0]['total_arts']} arts")
        
        return self.valid_builds


if __name__ == "__main__":
    # Example usage: Load settings and find builds

    # Load user settings
    with open('user_settings.json', 'r') as f:
        settings = json.load(f)

    # Extract settings
    character_name = settings['character']
    available_quartz = settings['selected_quartz']
    desired_arts = settings['selected_arts']

    # Load game data
    game_data = GameData()

    # Get character
    character = game_data.get_character(character_name)

    # Print loaded data
    print(f"Character: {character_name}")
    print(f"Available quartz: {len(available_quartz)}")
    print(f"Desired arts: {desired_arts}")

    # Create test quartz set with known relevant quartz + 3 others
    known_relevant = {"EP 2", "Septium Vein", "EP Cut 2",
                      "Topaz Shield", "Heal", "Sapphire Shield"}
    additional_quartz = {"Mind 1", "Attack 1",
                         "Defense 1"}  # 3 not in user's list
    quartz_set = known_relevant | additional_quartz

    print(f"\nTest quartz set: {quartz_set}")

    # Create finder and search for builds
    finder = BuildFinder(character, quartz_set, desired_arts, game_data)
    finder._print_info()
    builds = finder.find_builds()

    # Display results
    if builds:
        print(f"\nShowing first build:")
        first_build = builds[0]
        print(f"Elements: {first_build['elements']}")
        print(f"\nPlacements:")
        for placement in first_build['placements']:
            shared_marker = " (SHARED)" if placement['is_shared'] else ""
            print(
                f"  Line {placement['line_index']}, Slot {placement['slot_index']}{shared_marker}: {placement['quartz']}")
    else:
        print("\nNo valid builds found.")
