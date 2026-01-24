import tkinter as tk
from tkinter import messagebox, simpledialog
import threading
import time
import re
import ctypes

try:
    # Handle DPI awareness for 2K/4K screens
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    pass

try:
    from PIL import ImageGrab, Image
    import pytesseract
    from pynput import keyboard
except ImportError:
    # Fail silently here; the GUI will catch import errors when button is clicked
    pass

class PriceAcquisitionOverlay:
    """
    A minimal overlay to guide the user through capturing prices from the game window.
    """

    # Coordinates calibrated from 2K screen (User provided)
    # Region targeting the top price in the list (Left, Top, Right, Bottom)
    PRICE_REGION = (619, 205, 739, 245)

    def __init__(self, root, price_manager, on_close_callback, tasks=None, update_callback=None):
        self.root = root
        self.price_manager = price_manager
        self.on_close_callback = on_close_callback
        self.update_callback = update_callback

        self.overlay = None
        self.listener = None
        self.current_index = 0
        self.running = False

        if tasks is not None:
            self.tasks = tasks
        else:
            # Define the iteration grid (Must match gui.py order)
            self.stats = ["Base", "PS", "Attacco", "Difesa", "Attacco Speciale", "Difesa Speciale", "Velocità"]

            self.egg_groups_map = [
                ("Mostro", "Mostro"),
                ("Water A", "Water A"),
                ("Coleottero", "Coleottero"),
                ("Volante", "Volante"),
                ("Campo", "Campo"),
                ("Folletto", "Folletto"),
                ("Pianta", "Pianta"),
                ("Umanoide", "Umanoide"),
                ("Water C", "Water C"),
                ("Minerale", "Minerale"),
                ("Caos", "Caos"),
                ("Water B", "Water B"),
                ("Ditto", "Ditto"),
                ("Drago", "Drago")
            ]

            # Flatten the grid into a linear list of tasks
            self.tasks = []
            for display_name, category_key in self.egg_groups_map:
                for stat in self.stats:
                    # Determine gender based on category
                    gender = "X" if category_key == "Ditto" else "M"
                    self.tasks.append({
                        "stat": stat,
                        "display": f"{display_name}",
                        "category": category_key,
                        "gender": gender
                    })

    def start(self):
        """Minimizes main app and starts the overlay."""
        try:
            # pytesseract is already imported at top level
            from pynput import keyboard
        except ImportError:
            messagebox.showerror("Errore", "Librerie mancanti. Assicurati di aver installato: pytesseract, pynput, pillow")
            return

        self.root.iconify() # Minimize main window
        self.running = True
        self.current_index = 0

        self._create_overlay_window()
        self._start_keyboard_listener()
        self._update_display()

    def _create_overlay_window(self):
        self.overlay = tk.Toplevel(self.root)
        self.overlay.title("Acquisizione Prezzi")
        
        # Calculate Top-Right Position
        screen_width = self.root.winfo_screenwidth()
        window_width = 500 # Increased width for messages
        x_pos = screen_width - window_width
        
        self.overlay.geometry(f"{window_width}x300+{x_pos}+0") # Top-Right
        self.overlay.overrideredirect(True) # Remove window frame
        self.overlay.attributes("-topmost", True)
        self.overlay.configure(bg="#2c3e50")

        # Layout
        self.lbl_instruction = tk.Label(self.overlay, text="F10: Cattura | F9: Manuale | F11: Salta", font=("Arial", 10), fg="#ecf0f1", bg="#2c3e50")
        self.lbl_instruction.pack(pady=(10, 0))

        self.lbl_current_task = tk.Label(self.overlay, text="In attesa...", font=("Arial", 14, "bold"), fg="#f1c40f", bg="#2c3e50")
        self.lbl_current_task.pack(pady=2)
        
        # New Warning Label
        self.lbl_warning = tk.Label(self.overlay, text="", font=("Arial", 10, "bold"), fg="#e74c3c", bg="#2c3e50", wraplength=480)
        self.lbl_warning.pack(pady=0)
        
        # New Recommendation Label
        self.lbl_recommendation = tk.Label(self.overlay, text="", font=("Arial", 9), fg="#2ecc71", bg="#2c3e50", wraplength=480)
        self.lbl_recommendation.pack(pady=0)

        self.lbl_progress = tk.Label(self.overlay, text="0 / 0", font=("Arial", 9), fg="#bdc3c7", bg="#2c3e50")
        self.lbl_progress.pack(pady=(5, 10))

    def _start_keyboard_listener(self):
        self.listener = keyboard.Listener(on_release=self._on_key_release)
        self.listener.start()

    def _on_key_release(self, key):
        if not self.running:
            return False

        if key == keyboard.Key.f10:
            # Capture must be done on the main thread or handled carefully
            # Since pynput is a separate thread, we schedule the capture on the GUI thread
            self.overlay.after(0, self._capture_price)
        elif key == keyboard.Key.f11:
            self.overlay.after(0, self._skip_item)
        elif key == keyboard.Key.f9:
            self.overlay.after(0, self._manual_input)

    def _manual_input(self):
        """Opens a dialog for manual price entry."""
        if self.current_index >= len(self.tasks):
            return

        # simpledialog is modal, so it should block
        price = simpledialog.askinteger("Input Manuale", "Inserisci prezzo:", parent=self.overlay, minvalue=0)
        
        if price is not None:
             task = self.tasks[self.current_index]
             print(f"Manual Entry: {price} for {task['stat']} - {task['display']}")

             if self.update_callback:
                 self.update_callback(task, price)
             else:
                 self.price_manager.set_price(task['stat'], task['category'], task['gender'], price)

             # Advance
             self.current_index += 1
             if self.current_index >= len(self.tasks):
                 self._finish()
             else:
                 self._update_display()

    def _skip_item(self):
        if self.current_index >= len(self.tasks):
            return

        print(f"Skipped: {self.tasks[self.current_index]['display']}")
        self.current_index += 1

        if self.current_index >= len(self.tasks):
            self._finish()
        else:
            self._update_display()

    def _capture_price(self):
        if self.current_index >= len(self.tasks):
            return

        # 1. Grab Image
        try:
            screenshot = ImageGrab.grab(bbox=self.PRICE_REGION)

            # 2. OCR
            # Configuration: Assume single block of text, numeric priority
            custom_config = r'--psm 7 -c tessedit_char_whitelist=0123456789$,.'
            text = pytesseract.image_to_string(screenshot, config=custom_config)

            # 3. Parse Price
            price = self._parse_price(text)

            if price is not None:
                # 4. Save Logic
                task = self.tasks[self.current_index]
                print(f"Captured: {price} for {task['stat']} - {task['display']}")

                if self.update_callback:
                    self.update_callback(task, price)
                else:
                    self.price_manager.set_price(task['stat'], task['category'], task['gender'], price)

                # 5. Advance
                self.current_index += 1
                if self.current_index >= len(self.tasks):
                    self._finish()
                else:
                    self._update_display()
            else:
                # Visual feedback for failure
                self.lbl_instruction.config(text="Errore lettura! Riprova (F10)", fg="#e74c3c")
                self.overlay.after(1000, lambda: self.lbl_instruction.config(text="Premi F10 per catturare", fg="#ecf0f1"))

        except Exception as e:
            print(f"Error capturing: {e}")

    def _parse_price(self, text):
        """Cleans OCR text '$4,999' or '1.000' -> 4999, 1000"""
        if not text:
            return None

        # 1. Remove dots (thousands separators in some regions)
        # e.g. "1.000" -> "1000"
        text = text.replace('.', '')

        # 2. Remove '$', ',', ' ' and newlines using regex
        # Keep only digits
        clean = re.sub(r'[^\d]', '', text)

        if not clean:
            return None
        try:
            return int(clean)
        except ValueError:
            return None

    def _update_display(self):
        if self.current_index < len(self.tasks):
            task = self.tasks[self.current_index]
            text = f"CERCA: {task['stat'].upper()}\n{task['display'].upper()}"
            self.lbl_current_task.config(text=text)
            
            # Update Warning
            warn = task.get("warning")
            if warn:
                self.lbl_warning.config(text=warn)
            else:
                 self.lbl_warning.config(text="")
                 
            # Update Recommendation
            rec = task.get("recommendation")
            if rec:
                self.lbl_recommendation.config(text=rec)
            else:
                self.lbl_recommendation.config(text="")
            
            self.lbl_progress.config(text=f"{self.current_index + 1} / {len(self.tasks)}")

    def _finish(self):
        self.running = False
        if self.listener:
            self.listener.stop()

        if not self.update_callback:
            self.price_manager.save_prices()

        if self.overlay:
            self.overlay.destroy()

        self.root.deiconify() # Restore main window
        messagebox.showinfo("Completato", "Acquisizione prezzi completata!")

        if self.on_close_callback:
            self.on_close_callback()
