import unittest
from structures import PianoCompleto, PokemonRichiesto, Livello, Accoppiamento, PianoValutato
from plan_evaluator import PlanEvaluator
from price_manager import PriceManager
from gender_helper import GenderHelper

class TestGenderEvaluation(unittest.TestCase):
    def setUp(self):
        # Setup helpers
        self.pm = PriceManager()
        self.gh = GenderHelper()

        # Setup common prices
        # Default high price
        self.pm.set_price("PS", "Specie", "M", 20000)
        self.pm.set_price("PS", "Specie", "F", 20000)
        self.pm.set_price("PS", "EggGroup", "M", 20000)
        self.pm.set_price("PS", "Ditto", "X", 30000)

        # Mock Data
        self.pokemon_data = {
            "Garchomp": ["Drago", "Mostro"],
            "Squirtle": ["Mostro", "Water A"],
            "Nidoran♂": ["Mostro", "Campo"],
            "Vulpix": ["Campo"]
        }

    def test_leaf_optimization_male_helper(self):
        """
        If we need a Male Helper (EggGroup Drago), we should buy the cheapest option.
        If Target is Garchomp (50/50), cost M is 5000.
        If we force buying "Optimal Species M", it should use that price.
        """
        # Scenario: Need Male Drago for PS.
        # Price Manager has generic prices.
        self.pm.set_price("PS", "Specie", "M", 50000) # Garchomp M
        self.pm.set_price("PS", "EggGroup", "M", 5000) # Generic Drago M (e.g. Magikarp equivalent)

        # Create a dummy plan with 1 node (Male Helper)
        # Supply a legend so "PS" is recognized
        dummy_piano = PianoCompleto(1, [], None, {"PS": "PS"})

        ev = PlanEvaluator(dummy_piano, [], self.pm, "Garchomp", self.pokemon_data, None, self.gh)

        # Mock the maps
        ev._child_to_parents_map = {} # Leaf
        ev._node_map = {1: PokemonRichiesto(("PS",))}

        # Calculate cost for a Male Helper (is_species_mandatory=False)
        pv = PianoValutato(dummy_piano)
        cost, decisions = ev.calculate_cost_recursive(1, pv, is_species_mandatory=False)

        # Expectation: Should choose EggGroup M ($5000) over Specie M ($50000)
        self.assertEqual(cost, 5000)

        # Check that it recommends a Species.
        # "Drago" group optimal species logic will pick something.
        # Garchomp is in "Drago". 50/50 -> 5000 fee.
        # Dratini (not in mock data, but in JSON) is in "Drago". 50/50.
        # So "Comprare [SomeSpecies]"
        self.assertTrue(any("Comprare" in d for d in decisions.values()))

    def test_intermediate_gender_fee_logic(self):
        """
        Verify that intermediate nodes add the gender fee.
        Target: Bulbasaur (87.5% M).
        We need a Male Helper (intermediate).
        We calculate cost using Target Species (Conservative).
        Gender Fee for Bulbasaur M = $5000.
        """
        target = "Bulbasaur" # 87.5% M

        # Create Plan
        # Child (Helper M) <- P1 (Helper F) + P2 (Helper M)
        req_child = PokemonRichiesto(("PS", "Attacco")) # Intermediate
        req_p1 = PokemonRichiesto(("PS",))
        req_p2 = PokemonRichiesto(("Attacco",))

        acc = Accoppiamento(req_p1, req_p2, req_child)
        piano = PianoCompleto(1, [], None, {"PS":"PS", "Attacco":"Attacco"}, [Livello(1, [acc])])

        ev = PlanEvaluator(piano, [], self.pm, target, {"Bulbasaur": ["Mostro", "Pianta"]}, None, self.gh)
        ev._build_tree_maps()

        # Set prices so leaves are cheap
        self.pm.set_price("PS", "EggGroup", "M", 1000)
        self.pm.set_price("Attacco", "EggGroup", "M", 1000)
        # We need P1 (Mother) to be Female. "EggGroup F".
        self.pm.set_price("PS", "EggGroup", "F", 1000)
        # Wait, my logic for leaves:
        # P1 (Helper F) -> calculate_cost(P1, True) -> is_species_mandatory=True.
        # It treats P1 as "Target Species F".
        # So it looks up "Specie F".
        self.pm.set_price("PS", "Specie", "F", 2000) # Bulbasaur F (Leaf)

        # P2 (Helper M) -> calculate_cost(P2, False) -> is_species_mandatory=False.
        # It treats P2 as "Helper M".
        # It looks up "EggGroup M".

        # Calculate Cost for Child (Helper M)
        # We call calculate_cost_recursive(Child, False).
        # It is NOT mandatory.

        # Optimization Logic:
        # It picks "Optimal Species" for Group "Mostro".
        # It finds "Nidoran M".
        # Gender Fee for Nidoran M (Male) = 0.

        # Base Fee = 20000 (Item).
        # Cost P1 (Bulbasaur F) = 2000.
        # Cost P2 (EggGroup M) = 1000.

        # Expected Total = 2000 + 1000 + 20000 + 0 = 23000.

        pv = PianoValutato(piano)
        cost, _ = ev.calculate_cost_recursive(id(req_child), pv, is_species_mandatory=False)
        self.assertEqual(cost, 23000)

if __name__ == '__main__':
    unittest.main()
