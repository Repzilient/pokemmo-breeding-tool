from typing import Dict, Optional

class PriceManager:
    """
    Manages the session-based price list for Pokemon breeding components.
    Structure:
    prices[stat_name][category][gender] = price

    stat_name: "PS", "Attacco", ..., "Natura"
    category: "Specie", "EggGroup", "Ditto"
    gender: "M", "F", "X"
    """
    def __init__(self):
        # Data structure: Dict[Stat, Dict[Category, Dict[Gender, int]]]
        self.prices: Dict[str, Dict[str, Dict[str, int]]] = {}

    def set_price(self, stat_name: str, category: str, gender: str, price: int):
        if stat_name not in self.prices:
            self.prices[stat_name] = {}
        if category not in self.prices[stat_name]:
            self.prices[stat_name][category] = {}

        self.prices[stat_name][category][gender] = price

    def get_price(self, stat_name: str, category: str, gender: str) -> int:
        """
        Retrieves the price. Returns infinity (999999999) if not found.
        """
        try:
            return self.prices.get(stat_name, {}).get(category, {}).get(gender, 999999999)
        except AttributeError:
             return 999999999

    def clear(self):
        self.prices = {}
