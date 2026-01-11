import json
from typing import Dict, Optional, List, Tuple

class GenderHelper:
    def __init__(self, gender_file: str = 'pokemon_gender.json', data_file: str = 'pokemon_data.json'):
        self.gender_data: Dict[str, Dict] = {}
        self.egg_groups: Dict[str, List[str]] = {} # Map Group -> List of Species
        self.pokemon_data_raw: Dict[str, List[str]] = {} # Map Species -> List of Groups
        self.gender_file = gender_file
        self.data_file = data_file
        self._load_data()

    def _load_data(self):
        try:
            with open(self.gender_file, 'r', encoding='utf-8') as f:
                raw_list = json.load(f)
                # Normalize keys just in case
                for item in raw_list:
                    self.gender_data[item['name']] = item
        except FileNotFoundError:
            print(f"Warning: {self.gender_file} not found.")

        try:
            with open(self.data_file, 'r', encoding='utf-8') as f:
                self.pokemon_data_raw = json.load(f)

                # Build reverse map: EggGroup -> Species List
                for species, groups in self.pokemon_data_raw.items():
                    for group in groups:
                        if group not in self.egg_groups:
                            self.egg_groups[group] = []
                        self.egg_groups[group].append(species)
        except FileNotFoundError:
            print(f"Warning: {self.data_file} not found.")

    def get_gender_info(self, species_name: str) -> Optional[Dict]:
        return self.gender_data.get(species_name)

    def get_gender_ratio_type(self, species_name: str) -> str:
        info = self.gender_data.get(species_name)
        if not info:
            return "Unknown"
        return info.get('gender_ratio', 'Unknown')

    def get_gender_selection_cost(self, species_name: str, desired_gender: str) -> int:
        """
        Returns cost to select gender: 0, 5000, 9000, 21000.
        desired_gender: 'M', 'F', 'X' (Genderless/Don't care)
        """
        info = self.gender_data.get(species_name)
        if not info:
            return 999999 # Penalty for unknown

        ratio_str = info.get('gender_ratio', '')

        # Case 0: Fixed Gender / Genderless
        if ratio_str == "N/A":
            return 0
        if "100% M" in ratio_str:
            return 0 if desired_gender == 'M' else 999999
        if "100% F" in ratio_str:
            return 0 if desired_gender == 'F' else 999999

        if desired_gender == 'X':
            return 0

        # Parse ratios
        # "50% M, 50% F"
        # "87.5% M, 12.5% F"
        # "25% M, 75% F"
        # "75% M, 25% F"

        if "50% M" in ratio_str:
            return 5000

        if "87.5% M" in ratio_str:
            # Male is Common, Female is Rare
            if desired_gender == 'M': return 5000
            if desired_gender == 'F': return 21000

        if "25% M" in ratio_str:
            # Male is Rare, Female is Common
            if desired_gender == 'M': return 9000
            if desired_gender == 'F': return 5000

        if "75% M" in ratio_str:
             # Male is Common, Female is Rare/Medium
             # User rule: "75% M... Choose Male 5000, Choose Female 9000"
             if desired_gender == 'M': return 5000
             if desired_gender == 'F': return 9000

        # Fallback
        return 5000

    def get_optimal_species_for_egg_group(self, egg_group: str, desired_gender: str) -> str:
        """
        Finds the species in the egg group with the lowest cost for the desired gender.
        """
        candidates = self.egg_groups.get(egg_group, [])
        if not candidates:
            return "Unknown"

        best_species = None
        min_cost = 999999999

        # Heuristic: Prefer 100% gender, then high ratio, then 50/50.
        # Actually just use get_gender_selection_cost logic.

        for species in candidates:
            # Skip if data missing
            if species not in self.gender_data:
                continue

            cost = self.get_gender_selection_cost(species, desired_gender)

            # Optimization: If cost is 0, return immediately (can't beat that)
            if cost == 0:
                return species

            if cost < min_cost:
                min_cost = cost
                best_species = species

        return best_species if best_species else candidates[0]
