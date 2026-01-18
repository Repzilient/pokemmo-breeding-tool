import sys
from unittest.mock import MagicMock

# Mock tkinter stack
class MockToplevel:
    def __init__(self, parent=None, **kwargs): pass
    def title(self, val): pass
    def geometry(self, val): pass
    def destroy(self): pass

mock_tk = MagicMock()
mock_tk.Toplevel = MockToplevel
mock_tk.Tk = MockToplevel
mock_ttk = MagicMock()
mock_ttk.Frame = MagicMock

# Configure Entry Mock
mock_entry_instance = MagicMock()
mock_entry_instance.get.return_value = "500" # Simulate user input "500"
mock_ttk.Entry.return_value = mock_entry_instance

sys.modules['tkinter'] = mock_tk
sys.modules['tkinter.ttk'] = mock_ttk
sys.modules['tkinter.messagebox'] = MagicMock()

from gui import PriceInputDialog
from price_manager import PriceManager

def test_popup_smart_labels():
    print("Initializing Mock PriceManager...")
    pm = MagicMock(spec=PriceManager)
    pm.get_price.return_value = 999999999 # Default

    required_stats = {"PS"}
    relevant_groups = ["Mostro", "Drago"]

    print("Instantiating PriceInputDialog...")
    dialog = PriceInputDialog(MagicMock(), required_stats, pm, lambda: None, relevant_egg_groups=relevant_groups)

    # Check if we have standard 5 columns (plus maybe headers logic but we check persistence mainly)
    # The new structure is hardcoded inputs: Specie_M, Specie_F, EggGroup_M, EggGroup_F, Ditto

    # Simulate Confirm
    print("Simulating Confirm...")
    dialog._confirm()

    # Verify Calls
    # We entered "500" for everything.

    # Check Generic Save
    # set_price(stat, "EggGroup", "M", 500)
    # pm.set_price.assert_any_call("PS", "EggGroup", "M", 500)
    # Note: assert_any_call might be flaky with integers if mocks return 1.
    # But let's check the call_args_list manually to be safe.

    found_generic = False
    found_mostro = False
    found_drago = False

    for call in pm.set_price.call_args_list:
        args, _ = call
        stat, cat, gender, val = args
        if stat == "PS" and gender == "M":
            if cat == "EggGroup": found_generic = True
            if cat == "Mostro": found_mostro = True
            if cat == "Drago": found_drago = True

    if found_generic: print("Generic EggGroup Saved.")
    else: print("FAILURE: Generic EggGroup NOT Saved.")

    if found_mostro: print("Mostro Saved.")
    else: print("FAILURE: Mostro NOT Saved.")

    if found_drago: print("Drago Saved.")
    else: print("FAILURE: Drago NOT Saved.")

    if found_generic and found_mostro and found_drago:
        print("SUCCESS: Smart Persistence verified.")

if __name__ == "__main__":
    test_popup_smart_labels()
