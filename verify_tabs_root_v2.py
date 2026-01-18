import sys
from unittest.mock import MagicMock

# Mock Setup
class MockToplevel:
    def __init__(self, parent=None, **kwargs): pass
    def title(self, val): pass
    def geometry(self, val): pass
    def destroy(self): pass
    def pack(self, **kwargs): pass
    def grid(self, **kwargs): pass
    def add(self, widget, **kwargs): pass
    def columnconfigure(self, *args, **kwargs): pass
    def rowconfigure(self, *args, **kwargs): pass

mock_tk = MagicMock()
mock_tk.Tk = MockToplevel
mock_ttk = MagicMock()
mock_ttk.Notebook = MagicMock
mock_ttk.Frame = MagicMock
mock_ttk.Combobox = MagicMock

sys.modules['tkinter'] = mock_tk
sys.modules['tkinter.ttk'] = mock_ttk
sys.modules['tkinter.messagebox'] = MagicMock()

from gui import BreedingToolApp

def verify_main_window_root():
    print("Instantiating BreedingToolApp...")
    app = BreedingToolApp()

    if not hasattr(app, 'main_notebook'):
        print("FAILURE: 'main_notebook' not found.")
        return

    print("SUCCESS: Notebook found.")

    # Check tabs (mock calls)
    # app.main_notebook.add calls
    calls = app.main_notebook.add.call_count
    print(f"Tabs added: {calls}")
    if calls != 2:
        print(f"FAILURE: Expected 2 tabs, found {calls}")
        return

    print("SUCCESS: 2 Tabs confirmed.")
    print("ALL CHECKS PASSED.")

if __name__ == "__main__":
    verify_main_window_root()
