import json
import os
from typing import Dict, Any, Optional

PRICE_FILE = "prices.json"

class PriceManager:
    """
    Manages the price list for Pokemon breeding components.
    Structure:
    {
        "Specie": {
            "Charmander": {
                "M": {"1IV": 1000, "Nature": 2000, ...},
                "F": {"1IV": 5000, ...}
            }
        },
        "EggGroup": {
            "Mostro": {
                "M": {"1IV": 1000, ...},
                "F": {...}
            }
        },
        "Ditto": {
            "Ditto": {
                "X": {"1IV": 5000, ...} # X for Genderless
            }
        }
    }
    """
    def __init__(self, filepath: str = PRICE_FILE):
        self.filepath = filepath
        self.prices: Dict[str, Dict[str, Dict[str, Dict[str, int]]]] = {
            "Specie": {},
            "EggGroup": {},
            "Ditto": {}
        }
        self._load_prices()

    def _load_prices(self):
        if not os.path.exists(self.filepath):
            return
        try:
            with open(self.filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Merge loaded data with structure to ensure keys exist
                for cat in ["Specie", "EggGroup", "Ditto"]:
                    if cat in data:
                        self.prices[cat] = data[cat]
        except (json.JSONDecodeError, IOError):
            print(f"Warning: Could not load prices from {self.filepath}")

    def save_prices(self):
        try:
            with open(self.filepath, 'w', encoding='utf-8') as f:
                json.dump(self.prices, f, indent=4)
        except IOError as e:
            print(f"Error saving prices: {e}")

    def get_price(self, category: str, name: str, gender: str, price_type: str) -> int:
        """
        Retrieves the price. Returns 999,999,999 (infinity effectively) if not found,
        to discourage the algorithm from choosing a path with missing price data.
        """
        try:
            return self.prices.get(category, {}).get(name, {}).get(gender, {}).get(price_type, 999999999)
        except AttributeError:
             return 999999999

    def set_price(self, category: str, name: str, gender: str, price_type: str, price: int):
        if category not in self.prices:
            self.prices[category] = {}
        if name not in self.prices[category]:
            self.prices[category][name] = {}
        if gender not in self.prices[category][name]:
            self.prices[category][name][gender] = {}

        self.prices[category][name][gender][price_type] = price
        self.save_prices()

    def get_all_prices_for(self, category: str, name: str, gender: str) -> Dict[str, int]:
        return self.prices.get(category, {}).get(name, {}).get(gender, {})
