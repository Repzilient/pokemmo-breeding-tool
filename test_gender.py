from gender_helper import GenderHelper
import unittest

class TestGenderHelper(unittest.TestCase):
    def setUp(self):
        self.helper = GenderHelper()

    def test_load_data(self):
        self.assertIn("Bulbasaur", self.helper.gender_data)
        self.assertIn("Nidoran♀", self.helper.gender_data)

    def test_costs_50_50(self):
        # Pikachu 50/50
        self.assertEqual(self.helper.get_gender_selection_cost("Pikachu", "M"), 5000)
        self.assertEqual(self.helper.get_gender_selection_cost("Pikachu", "F"), 5000)

    def test_costs_87_12(self):
        # Bulbasaur 87.5% M
        self.assertEqual(self.helper.get_gender_selection_cost("Bulbasaur", "M"), 5000)
        self.assertEqual(self.helper.get_gender_selection_cost("Bulbasaur", "F"), 21000)

    def test_costs_25_75(self):
        # Vulpix 25% M / 75% F
        self.assertEqual(self.helper.get_gender_selection_cost("Vulpix", "M"), 9000)
        self.assertEqual(self.helper.get_gender_selection_cost("Vulpix", "F"), 5000)

    def test_costs_75_25(self):
        # Growlithe 75% M / 25% F
        self.assertEqual(self.helper.get_gender_selection_cost("Growlithe", "M"), 5000)
        self.assertEqual(self.helper.get_gender_selection_cost("Growlithe", "F"), 9000)

    def test_costs_fixed(self):
        # Nidoran M (100% M)
        self.assertEqual(self.helper.get_gender_selection_cost("Nidoran♂", "M"), 0)
        self.assertEqual(self.helper.get_gender_selection_cost("Nidoran♂", "F"), 999999)

        # Genderless
        self.assertEqual(self.helper.get_gender_selection_cost("Magnemite", "M"), 0) # Treated as N/A -> 0 (User said "No cost to pair")
        self.assertEqual(self.helper.get_gender_selection_cost("Magnemite", "X"), 0)

    def test_optimal_species(self):
        # Assuming Monster group has both 50/50 and 87.5/12.5 species
        # If I want a Male from Monster group:
        # Nidoran M is in Monster/Field. Cost 0.
        best_male = self.helper.get_optimal_species_for_egg_group("Mostro", "M")
        self.assertEqual(self.helper.get_gender_selection_cost(best_male, "M"), 0)

        # If I want a Female from Monster group:
        # Nidoran F is 100% F. Cost 0.
        best_female = self.helper.get_optimal_species_for_egg_group("Mostro", "F")
        self.assertEqual(self.helper.get_gender_selection_cost(best_female, "F"), 0)

if __name__ == '__main__':
    unittest.main()
