import json
import os
from typing import Dict, Optional

class PriceManager:
    """
    Manages the session-based price list for Pokemon breeding components.
    Structure:
    prices[stat_name][category][gender] = price

    stat_name: "PS", "Attacco", ..., "Natura", "Base"
    category: "Specie", "EggGroup", "Ditto"
    gender: "M", "F", "X"
    """
    FILE_PATH = os.path.join("data", "market_prices.json")
    DEFAULT_PRICE = 999999999

    # Mapping: Italian (App) -> English (DB)
    TRANSLATION_MAP = {
        "Mostro": "Monster",
        "Water A": "Water A",
        "Coleottero": "Bug",
        "Volante": "Flying",
        "Campo": "Field",
        "Folletto": "Fairy",
        "Pianta": "Plant",
        "Umanoide": "Humanoid",
        "Water C": "Water C",
        "Minerale": "Mineral",
        "Caos": "Chaos",
        "Water B": "Water B",
        "Ditto": "Ditto",
        "Drago": "Dragon"
    }

    def __init__(self, language: str = "IT"):
        # Data structure: Dict[Stat, Dict[Category, Dict[Gender, int]]]
        self.prices: Dict[str, Dict[str, Dict[str, int]]] = {}
        self.language = language
        self.load_prices()

    def _get_translated_category(self, category: str) -> str:
        """
        Translates the category based on the current language setting.
        Default is IT -> EN (for DB compatibility).
        """
        if self.language == "IT":
            return self.TRANSLATION_MAP.get(category, category)
        return category

    def normalize_prices(self):
        """
        Ensures strict JSON structure:
        1. Removes generic 'EggGroup' key.
        2. Ensures 'M' and 'F' keys for standard categories.
        3. Ensures 'X' key for Ditto.
        4. Fills missing values with DEFAULT_PRICE.
        """
        for stat in self.prices:
            # 1. Eliminate Generic EggGroup
            if "EggGroup" in self.prices[stat]:
                del self.prices[stat]["EggGroup"]

            for category in self.prices[stat]:
                # Skip if we just deleted it (safety check, though dict iteration is robust in copies usually, here we iterate keys)
                if category == "EggGroup":
                    continue

                if category == "Ditto":
                    if "X" not in self.prices[stat][category]:
                        self.prices[stat][category]["X"] = self.DEFAULT_PRICE
                else:
                    # Specific Species or Egg Groups
                    if "M" not in self.prices[stat][category]:
                        self.prices[stat][category]["M"] = self.DEFAULT_PRICE
                    if "F" not in self.prices[stat][category]:
                        self.prices[stat][category]["F"] = self.DEFAULT_PRICE

    def set_price(self, stat_name: str, category: str, gender: str, price: int):
        # Translate category to ensure consistency (IT -> EN)
        mapped_category = self._get_translated_category(category)

        if stat_name not in self.prices:
            self.prices[stat_name] = {}
        if mapped_category not in self.prices[stat_name]:
            self.prices[stat_name][mapped_category] = {}

        self.prices[stat_name][mapped_category][gender] = price

    def get_price(self, stat_name: str, category: str, gender: str) -> int:
        """
        Retrieves the price. Returns infinity (999999999) if not found.
        Automatically handles translation if enabled.
        """
        # Translate category if needed (e.g. Mostro -> Monster)
        mapped_category = self._get_translated_category(category)
        
        try:
            return self.prices.get(stat_name, {}).get(mapped_category, {}).get(gender, 999999999)
        except AttributeError:
             return 999999999

    def clear(self):
        self.prices = {}
        self.save_prices()

    def save_prices(self):
        self.normalize_prices()
        try:
            with open(self.FILE_PATH, 'w', encoding='utf-8') as f:
                json.dump(self.prices, f, indent=4)
        except IOError as e:
            print(f"Error saving prices: {e}")

    def load_prices(self):
        if not os.path.exists(self.FILE_PATH):
            return

        try:
            with open(self.FILE_PATH, 'r', encoding='utf-8') as f:
                self.prices = json.load(f)
            self.normalize_prices()
        except (IOError, json.JSONDecodeError) as e:
            print(f"Error loading prices: {e}")
            self.prices = {}
