import tkinter as tk
import os
from tkinter import ttk, messagebox
import json
import uuid
import copy
from typing import Set, List
import logging
import datetime
import bisect

# Importa le classi e le funzioni necessarie dai file del progetto
# Aggiornamento: Gestione automatica sesso e ottimizzazione costi
from structures import PokemonPosseduto, PokemonRichiesto, PianoValutato
import core_engine
import plan_evaluator
from price_manager import PriceManager
from market_overlay import PriceAcquisitionOverlay
import tesseract_setup  # [NEW] Import setup module

# [NEW] Setup Tesseract immediately on startup
tesseract_setup.setup_tesseract()


# --- Classe AutocompleteCombobox ---
class AutocompleteCombobox(ttk.Combobox):
    def set_completion_list(self, completion_list):
        self._completion_list = sorted(completion_list, key=str.lower)
        self._hits = []
        self._hit_index = 0
        self.position = 0
        self.bind('<KeyRelease>', self.handle_keyrelease)
        self['values'] = self._completion_list

    def autocomplete(self, delta=0):
        if delta:
            self.delete(self.position, tk.END)
        else:
            self.position = len(self.get())

        _hits = []
        prefix = self.get().lower()

        if not prefix:
            _hits = self._completion_list[:]
        else:
            # Optimized search using binary search (bisect)
            start_index = bisect.bisect_left(self._completion_list, prefix, key=str.lower)
            for i in range(start_index, len(self._completion_list)):
                element = self._completion_list[i]
                if element.lower().startswith(prefix):
                    _hits.append(element)
                else:
                    # List is sorted, so we can stop as soon as prefix doesn't match
                    break

        if _hits != self._hits:
            self._hit_index = 0
            self._hits = _hits

        if _hits:
            self._hit_index = (self._hit_index + delta) % len(self._hits)
            self.delete(0, tk.END)
            self.insert(0, self._hits[self._hit_index])
            self.select_range(self.position, tk.END)

    def handle_keyrelease(self, event):
        if event.keysym in ("Up", "Down"):
            self.autocomplete(delta=1 if event.keysym == "Down" else -1)
            return
        if event.keysym == "BackSpace":
            self.delete(self.index(tk.INSERT) -1, tk.END)
            self.position = self.index(tk.END)
        if len(event.keysym) == 1:
            self.autocomplete()


class PriceInputDialog(tk.Toplevel):
    """
    Dialog window for entering prices for specific required stats.
    Reverted to original 5-column grid layout with Smart Labels.
    """
    def __init__(self, parent, required_stats: Set[str], price_manager: PriceManager, on_confirm, relevant_egg_groups: List[str] = None, target_species: str = "", target_nature: str = None, pokemon_data: dict = None, gender_data: dict = None):
        super().__init__(parent)
        self.title("Inserimento Prezzi di Mercato")
        self.geometry("900x600")
        self.price_manager = price_manager
        self.on_confirm = on_confirm
        self.required_stats = sorted(list(required_stats))
        if "Base" not in self.required_stats:
            self.required_stats.insert(0, "Base")

        # Relevant groups for Smart Labels (e.g., ["Drago", "Mostro"])
        self.relevant_egg_groups = relevant_egg_groups if relevant_egg_groups else []
        self.target_species = target_species
        self.target_nature = target_nature
        self.pokemon_data = pokemon_data if pokemon_data else {}
        self.gender_data = gender_data if gender_data else {}

        self.inputs = {}
        self._create_widgets()

    def _create_widgets(self):
        container = ttk.Frame(self, padding="10")
        container.pack(fill="both", expand=True)

        ttk.Label(container, text="Inserisci i prezzi per gli ingredienti mancanti ($)", font=("Arial", 12, "bold")).pack(pady=10)

        # Scrollable Frame for inputs
        canvas = tk.Canvas(container)
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Smart Label Logic
        egg_group_label_m = "Egg Group (M)"
        egg_group_label_f = "Egg Group (F)"

        if self.relevant_egg_groups:
            joined_groups = "/".join(self.relevant_egg_groups)
            egg_group_label_m = f"{joined_groups} (M)"
            egg_group_label_f = f"{joined_groups} (F)"

        # Headers: Specie M, Specie F, EggGroup M (Smart), EggGroup F (Smart), Ditto
        headers = ["Statistica / Natura", "Specie (M)", "Specie (F)", egg_group_label_m, egg_group_label_f, "Ditto"]
        for col, text in enumerate(headers):
            ttk.Label(scrollable_frame, text=text, font=("Arial", 10, "bold")).grid(row=0, column=col, padx=5, pady=5)

        # Rows
        for i, stat in enumerate(self.required_stats):
            row = i + 1
            ttk.Label(scrollable_frame, text=stat).grid(row=row, column=0, padx=5, pady=5, sticky="w")

            self.inputs[stat] = {}

            def create_entry(category, gender, col):
                entry = ttk.Entry(scrollable_frame, width=10)
                entry.grid(row=row, column=col, padx=2)

                val = 999999999

                # Rule: Specie and Natura must ALWAYS be empty
                if category == "Specie" or stat == "Natura":
                    val = 999999999

                # Smart Pre-fill for Egg Groups
                elif category == "EggGroup" and self.relevant_egg_groups:
                    # Find lowest price among all relevant specific groups
                    min_price = 999999999

                    # Check Specific Groups
                    for group in self.relevant_egg_groups:
                        p = self.price_manager.get_price(stat, group, gender)
                        if p != 999999999 and p < min_price:
                            min_price = p

                    if min_price != 999999999:
                        val = min_price
                else:
                    # Standard Lookup (e.g. Ditto)
                    val = self.price_manager.get_price(stat, category, gender)

                if val != 999999999:
                    entry.insert(0, str(val))
                return entry

            # Specie M
            self.inputs[stat]["Specie_M"] = create_entry("Specie", "M", 1)

            # Specie F
            self.inputs[stat]["Specie_F"] = create_entry("Specie", "F", 2)

            # EggGroup M
            self.inputs[stat]["EggGroup_M"] = create_entry("EggGroup", "M", 3)

            # EggGroup F
            self.inputs[stat]["EggGroup_F"] = create_entry("EggGroup", "F", 4)

            # Ditto
            self.inputs[stat]["Ditto"] = create_entry("Ditto", "X", 5)

        # Button Frame
        btn_frame = ttk.Frame(container)
        btn_frame.pack(pady=20)

        # Confirm Button
        ttk.Button(btn_frame, text="Calcola Costi e Valuta", command=self._confirm).pack(side="left", padx=10)

        # Skip Prices Button
        ttk.Button(btn_frame, text="Non aggiungere prezzi", command=self._skip_prices).pack(side="left", padx=10)

        # Assistant Button
        ttk.Button(btn_frame, text="Avvia Assistente Acquisizione", command=self._start_assistant).pack(side="left", padx=10)

    def _start_assistant(self):
        """Starts the Overlay Assistant with a smart task list based on the current dialog."""
        tasks = []

        # Helper to create a task
        def add_task(stat, category, gender, display_text, widget_key, **kwargs):
             tasks.append({
                "stat": stat,
                "category": category,
                "gender": gender,
                "display": display_text,
                "widget_key": widget_key, # (stat, key_in_inputs_dict)
                "warning": kwargs.get("warning"),
                "recommendation": kwargs.get("recommendation")
             })

        # Helper to process gender ratio strings
        def get_gender_info(species_name):
             # Normalize name for lookup (handle lowercase anomalies in data)
             search_key = species_name
             if search_key not in self.gender_data:
                 search_key = species_name.capitalize()
             
             if search_key not in self.gender_data:
                 # Try title case just in case
                 search_key = species_name.title()

             if search_key not in self.gender_data:
                 return None, None
             
             data = self.gender_data[search_key]
             ratio_str = data.get("gender_ratio", "")
             
             is_female_only = "0% M, 100% F" in ratio_str
             is_male_only = "100% M, 0% F" in ratio_str
             
             # Extract Male %
             male_pct = 0
             try:
                 parts = ratio_str.split("% M")
                 if len(parts) > 0:
                     male_pct_str = parts[0].strip()
                     # Handle "87.5"
                     male_pct = float(male_pct_str)
             except:
                 pass
                 
             return is_female_only, male_pct

        # Helper to get Egg Group Recommendations/Warnings
        def get_group_advice(group, required_gender):
             if not self.pokemon_data or not self.gender_data:
                 return None, None
             
             candidates = []
             for name, groups in self.pokemon_data.items():
                 if group in groups:
                     candidates.append(name)
             
             warnings = []
             recommendations = []
             
             for name in candidates:
                 is_female_only, male_pct = get_gender_info(name)
                 
                 # LOGIC CHANGE: EVERYTHING only for FEMALE scans
                 if required_gender == "F":
                     # Warning: Female Only (Cannot produce Male)
                     if is_female_only:
                         warnings.append(name.capitalize())
                     
                     # Recommendation: High Male Ratio (Good for producing Male)
                     if male_pct is not None and male_pct >= 75: 
                         recommendations.append(f"{name.capitalize()} ({male_pct}% M)")
             
             warning_msg = None
             rec_msg = None
             
             if warnings:
                 # SHOW ALL WARNINGS
                 shown = ", ".join(sorted(warnings))
                 warning_msg = f"⚠️ EVITA: {shown} (Solo Femmina - Vicolo Cieco)"
                 
             if recommendations:
                 rec_sorted = sorted(recommendations, key=lambda x: x.split('(')[0])
                 shown = ", ".join(rec_sorted[:5])
                 if len(rec_sorted) > 5: shown += ", ..."
                 rec_msg = f"✅ CONSIGLIATI: {shown}"
                 
             return warning_msg, rec_msg

        # Generate Tasks Column-First

        # 1. Specie M
        for stat in self.required_stats:
             display = f"SPECIE: {self.target_species} (M)"
             warning = None
             
             # Specie Logic: Warning if target is Female Only (User can't find a Male!)
             is_f_only, _ = get_gender_info(self.target_species)
             if is_f_only:
                 warning = "⚠️ IMPOSSIBILE: Specie solo Femmina."
                 
             if stat == "Natura" and self.target_nature:
                 display += f" - NATURA: {self.target_nature}"
             else:
                 display += f" - {stat}"
             add_task(stat, "Specie", "M", display, (stat, "Specie_M"), warning=warning)

        # 2. Specie F
        for stat in self.required_stats:
             display = f"SPECIE: {self.target_species} (F)"
             warning = None
             # No specific warnings for Specie F usually
             
             if stat == "Natura" and self.target_nature:
                 display += f" - NATURA: {self.target_nature}"
             else:
                 display += f" - {stat}"
             add_task(stat, "Specie", "F", display, (stat, "Specie_F"), warning=warning)

        # 3. Egg Groups (M)
        if self.relevant_egg_groups:
            for group in self.relevant_egg_groups:
                # Calculate Advice (Recommendations mostly)
                w_msg, r_msg = get_group_advice(group, "M")
                
                for stat in self.required_stats:
                    display = f"GRUPPO: {group} (M)"
                    if stat == "Natura" and self.target_nature:
                        display += f" - NATURA: {self.target_nature}"
                    else:
                        display += f" - {stat}"

                    add_task(stat, group, "M", display, (stat, "EggGroup_M"), warning=w_msg, recommendation=r_msg)

        # 4. Egg Groups (F)
        if self.relevant_egg_groups:
            for group in self.relevant_egg_groups:
                # Calculate Advice (Warnings mostly)
                w_msg, r_msg = get_group_advice(group, "F")

                for stat in self.required_stats:
                    display = f"GRUPPO: {group} (F)"
                    if stat == "Natura" and self.target_nature:
                        display += f" - NATURA: {self.target_nature}"
                    else:
                        display += f" - {stat}"

                    add_task(stat, group, "F", display, (stat, "EggGroup_F"), warning=w_msg, recommendation=r_msg)

        # 5. Ditto
        for stat in self.required_stats:
             display = f"DITTO"
             if stat == "Natura" and self.target_nature:
                 display += f" - NATURA: {self.target_nature}"
             else:
                 display += f" - {stat}"
             add_task(stat, "Ditto", "X", display, (stat, "Ditto"))

        # Start Overlay
        overlay = PriceAcquisitionOverlay(
            self,
            self.price_manager,
            None, # No close callback needed for popup mode
            tasks=tasks,
            update_callback=self._on_assistant_update
        )
        overlay.start()

    def _on_assistant_update(self, task, price):
        """Callback to update the UI directly."""
        stat, key = task["widget_key"]
        if stat in self.inputs and key in self.inputs[stat]:
            entry = self.inputs[stat][key]

            # Check current value
            current_val_str = entry.get().strip()
            current_val = 999999999
            if current_val_str:
                try:
                    current_val = int(current_val_str)
                except ValueError:
                    pass

            # Update if empty or lower
            if price < current_val:
                entry.delete(0, tk.END)
                entry.insert(0, str(price))

    def _confirm(self):
        # Create a temporary copy of the PriceManager for THIS calculation only.
        # This prevents polluting the persistent DB with specific breed overrides or dual-group conflicts.
        temp_pm = copy.deepcopy(self.price_manager)

        for stat, entries in self.inputs.items():
            try:
                def get_val(entry):
                    val = entry.get().strip()
                    if not val: return 999999999
                    return int(val)

                # Save Specie
                temp_pm.set_price(stat, "Specie", "M", get_val(entries["Specie_M"]))
                temp_pm.set_price(stat, "Specie", "F", get_val(entries["Specie_F"]))

                # Save Egg Groups
                eg_m = get_val(entries["EggGroup_M"])
                eg_f = get_val(entries["EggGroup_F"])

                # Save to ALL relevant specific groups in the TEMP manager
                # This ensures that for Dual Groups, the price is available regardless of which path the optimizer takes.
                if self.relevant_egg_groups:
                    for group in self.relevant_egg_groups:
                        temp_pm.set_price(stat, group, "M", eg_m)
                        temp_pm.set_price(stat, group, "F", eg_f)

                # Save Ditto
                temp_pm.set_price(stat, "Ditto", "X", get_val(entries["Ditto"]))

            except ValueError:
                messagebox.showerror("Errore", f"Inserisci valori numerici validi per {stat}")
                return

        # Do NOT save to disk. Pass the temporary manager to the evaluator.
        # Log the prices used for this specific calculation
        try:
             logging.info(f"PRICES CONFIRMED (Session Only):\n{json.dumps(temp_pm.prices, indent=2)}")
        except Exception as e:
             logging.error(f"Failed to log prices: {e}")

        self.on_confirm(temp_pm)
        self.destroy()

    def _skip_prices(self):
        # Only reset Species prices for this run
        for stat in self.required_stats:
            self.price_manager.set_price(stat, "Specie", "M", 0)
            self.price_manager.set_price(stat, "Specie", "F", 0)

        self.on_confirm()
        self.destroy()


class BreedingToolApp(tk.Tk):
    """
    Interfaccia grafica per lo strumento di pianificazione del breeding di PokeMMO.
    """
    def __init__(self):
        super().__init__()
        self.title("PokeMMO Breeding Planner")
        self.geometry("1200x800")

        # [NEW] delayed health check display
        if not tesseract_setup.verify_tesseract_available():
             messagebox.showwarning(
                "Tesseract OCR Mancante",
                "Impossibile trovare Tesseract OCR nella cartella del progetto.\n"
                "Le funzionalità di scansione dei prezzi non saranno disponibili.\n\n"
                "Assicurati che la cartella 'Tesseract-OCR' sia presente."
            )

        # --- Caricamento Dati ---
        self.pokemon_names = []
        self.pokemon_data = {}
        self.natures = [
            "Nessuna", "Adamant", "Modest", "Jolly", "Timid", "Bold", "Calm",
            "Impish", "Careful", "Brave", "Quiet", "Rash", "Mild", "Hasty",
            "Serious", "Docile", "Hardy", "Bashful", "Quirky", "Lonely",
            "Naughty", "Gentle", "Lax", "Relaxed", "Sassy"
        ]
        self.stats = ["PS", "Attacco", "Difesa", "Attacco Speciale", "Difesa Speciale", "Velocità"]
        self.gender_data = {}
        self._load_pokemon_data()
        self._load_gender_data()

        self.price_manager = PriceManager()

        # --- Variabili di stato ---
        self.owned_pokemon_list = []
        self.target_ivs_vars = {stat: tk.BooleanVar() for stat in self.stats}
        self.owned_ivs_vars = {stat: tk.BooleanVar() for stat in self.stats}
        self.target_nature_var = tk.StringVar(value=self.natures[0])
        self.owned_nature_var = tk.StringVar(value=self.natures[0])
        self.target_species_var = tk.StringVar()
        self.owned_species_var = tk.StringVar()
        self.owned_gender_var = tk.StringVar(value="Maschio")

        # Stored generated plans for phase 2
        self.generated_plans_cache = []

        # --- Setup Logging ---
        log_dir = "debug"
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)

        logging.basicConfig(
            filename=os.path.join(log_dir, "gui_events.log"),
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            encoding='utf-8' # Force UTF-8 for special characters
        )
        # Clear log on startup
        with open(os.path.join("debug", "gui_events.log"), 'w'):
             pass
        logging.info("Application Started")

        # --- Creazione dell'interfaccia ---
        self._create_widgets()

    def _log_state(self, action_name: str):
        """Logs the current application state for debugging."""
        try:
            state_dump = {
                "action": action_name,
                "timestamp": str(datetime.datetime.now()),
                "target": {
                    "species": self.target_species_var.get(),
                    "nature": self.target_nature_var.get(),
                    "ivs": [s for s, v in self.target_ivs_vars.items() if v.get()]
                },
                "owned_pokemon": [
                   {
                       "specie": p.specie,
                       "sesso": p.sesso,
                       "natura": p.natura,
                       "ivs": p.ivs,
                       "id": p.id_utente
                   } for p in self.owned_pokemon_list
                ],
                "prices": self.price_manager.prices
            }
            logging.info(f"STATE DUMP [{action_name}]:\n{json.dumps(state_dump, indent=2)}")
        except Exception as e:
            logging.error(f"Failed to log state: {e}")

    def _load_pokemon_data(self):
        try:
            with open(os.path.join('data', 'pokemon_data.json'), 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.pokemon_data = data
                self.pokemon_names = sorted(data.keys())
        except FileNotFoundError:
            messagebox.showerror("Errore", "File 'pokemon_data.json' non trovato.")
            self.destroy()
        except json.JSONDecodeError:
            messagebox.showerror("Errore", "Il file 'pokemon_data.json' non è formattato correttamente.")
            self.destroy()

    def _load_gender_data(self):
        try:
            with open(os.path.join('data', 'pokemon_gender.json'), 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Crea una mappa {nome: dati_sesso}
                for entry in data:
                    self.gender_data[entry['name']] = entry
        except FileNotFoundError:
            messagebox.showwarning("Avviso", "File 'pokemon_gender.json' non trovato. Funzionalità automatica sesso disabilitata.")
        except json.JSONDecodeError:
            messagebox.showwarning("Avviso", "File 'pokemon_gender.json' corrotto.")

    def _create_widgets(self):
        # Create Main Notebook (Root Component)
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True)

        # Tab 1: Pianificatore
        self.tab_planner = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_planner, text="Pianificatore")
        self._setup_planner_tab(self.tab_planner)

        # Tab 2: Mercato GTL
        self.tab_gtl = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_gtl, text="Mercato GTL")
        self._setup_gtl_tab(self.tab_gtl)

    def _setup_planner_tab(self, parent):
        main_frame = ttk.Frame(parent, padding="10")
        main_frame.pack(fill="both", expand=True)

        left_frame = ttk.Frame(main_frame, padding="10")
        left_frame.pack(side="left", fill="y", padx=(0, 10))

        right_frame = ttk.Frame(main_frame, padding="10")
        right_frame.pack(side="right", fill="both", expand=True)

        self._create_target_section(left_frame)
        self._create_owned_section(left_frame)
        self._create_actions_section(left_frame)
        self._create_results_section(right_frame)

    def _setup_gtl_tab(self, parent):
        container = ttk.Frame(parent, padding="10")
        container.pack(fill="both", expand=True)

        # Use Grid layout consistently for container
        ttk.Label(container, text="Mercato GTL (Salvataggio Permanente)", font=("Arial", 12, "bold")).grid(row=0, column=0, columnspan=2, pady=10, sticky="ew")

        # Scrollable Frame
        canvas = tk.Canvas(container)
        v_scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        h_scrollbar = ttk.Scrollbar(container, orient="horizontal", command=canvas.xview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)

        # Grid placement (Row 1 is the main content)
        canvas.grid(row=1, column=0, sticky="nsew")
        v_scrollbar.grid(row=1, column=1, sticky="ns")
        h_scrollbar.grid(row=2, column=0, sticky="ew")

        container.rowconfigure(1, weight=1) # Give weight to canvas row
        container.columnconfigure(0, weight=1) # Give weight to canvas column

        # Fixed Stats for GTL
        gtl_stats = ["Base", "PS", "Attacco", "Difesa", "Attacco Speciale", "Difesa Speciale", "Velocità"]

        # Egg Groups (Display -> Internal Key)
        egg_groups_map = [
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

        # Headers
        ttk.Label(scrollable_frame, text="Stat", font=("Arial", 9, "bold")).grid(row=0, column=0, padx=5, pady=5)
        for col_idx, (display_name, key) in enumerate(egg_groups_map):
            ttk.Label(scrollable_frame, text=display_name, font=("Arial", 9, "bold")).grid(row=0, column=col_idx + 1, padx=2, pady=5)

        # Rows
        self.gtl_inputs = {}
        for row_idx, stat in enumerate(gtl_stats):
            row = row_idx + 1
            ttk.Label(scrollable_frame, text=stat).grid(row=row, column=0, padx=5, pady=2, sticky="w")

            self.gtl_inputs[stat] = {}

            for col_idx, (display_name, key) in enumerate(egg_groups_map):
                entry = ttk.Entry(scrollable_frame, width=8)
                entry.grid(row=row, column=col_idx + 1, padx=1, pady=1)

                # Determine gender/category
                category = key
                gender = "X" if key == "Ditto" else "M"

                val = self.price_manager.get_price(stat, category, gender)
                if val != 999999999:
                    entry.insert(0, str(val))

                # Bind events to save
                entry.bind("<FocusOut>", lambda e, s=stat, c=category, g=gender, ent=entry: self._save_gtl_price(s, c, g, ent))
                entry.bind("<Return>", lambda e, s=stat, c=category, g=gender, ent=entry: self._save_gtl_price(s, c, g, ent))

                self.gtl_inputs[stat][key] = entry

        # Save Button (Explicit)
        btn_frame = ttk.Frame(parent)
        btn_frame.pack(pady=5)
        ttk.Button(btn_frame, text="Salva Prezzi GTL", command=self.price_manager.save_prices).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Acquisizione Prezzi (Auto)", command=self._start_auto_acquisition).pack(side="left", padx=5)

    def _start_auto_acquisition(self):
        overlay = PriceAcquisitionOverlay(self, self.price_manager, self._refresh_gtl_view)
        overlay.start()

    def _refresh_gtl_view(self):
        """Reloads prices from PriceManager into the GTL input fields."""
        # Fixed Stats for GTL
        gtl_stats = ["Base", "PS", "Attacco", "Difesa", "Attacco Speciale", "Difesa Speciale", "Velocità"]

        # Egg Groups (Display -> Internal Key)
        egg_groups_map = [
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

        for stat in gtl_stats:
            for _, key in egg_groups_map:
                 # Determine gender/category
                category = key
                gender = "X" if key == "Ditto" else "M"

                val = self.price_manager.get_price(stat, category, gender)

                entry = self.gtl_inputs.get(stat, {}).get(key)
                if entry:
                    entry.delete(0, tk.END)
                    if val != 999999999:
                        entry.insert(0, str(val))

    def _save_gtl_price(self, stat, category, gender, entry_widget):
        try:
            val_str = entry_widget.get().strip()
            if not val_str:
                val = 999999999
            else:
                val = int(val_str)
            self.price_manager.set_price(stat, category, gender, val)
        except ValueError:
            pass # Ignore invalid input during focus out

    def _create_target_section(self, parent):
        target_frame = ttk.LabelFrame(parent, text="Pokémon Target", padding="10")
        target_frame.grid(row=0, column=0, sticky="ew", pady=5)
        target_frame.columnconfigure(1, weight=1)

        ttk.Label(target_frame, text="Specie:").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        target_combo = AutocompleteCombobox(target_frame, textvariable=self.target_species_var)
        target_combo.set_completion_list(self.pokemon_names)
        target_combo.grid(row=0, column=1, sticky="ew", padx=5, pady=2)

        ttk.Label(target_frame, text="IVs Desiderate:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        iv_frame = ttk.Frame(target_frame)
        iv_frame.grid(row=1, column=1, sticky="ew")
        for i, stat in enumerate(self.stats):
            ttk.Checkbutton(iv_frame, text=stat, variable=self.target_ivs_vars[stat]).grid(row=i//3, column=i%3, sticky="w", padx=5)

        ttk.Label(target_frame, text="Natura:").grid(row=2, column=0, sticky="w", padx=5, pady=2)
        nature_combo = ttk.Combobox(target_frame, textvariable=self.target_nature_var, values=self.natures, state="readonly")
        nature_combo.grid(row=2, column=1, sticky="ew", padx=5, pady=2)

    def _create_owned_section(self, parent):
        owned_frame = ttk.LabelFrame(parent, text="Pokémon Posseduti", padding="10")
        owned_frame.grid(row=1, column=0, sticky="ew", pady=5)
        owned_frame.columnconfigure(0, weight=1)

        add_form = ttk.Frame(owned_frame)
        add_form.grid(row=0, column=0, sticky="ew")
        add_form.columnconfigure(1, weight=1)

        ttk.Label(add_form, text="Specie:").grid(row=0, column=0, sticky="w")
        owned_combo = AutocompleteCombobox(add_form, textvariable=self.owned_species_var)
        owned_combo.set_completion_list(self.pokemon_names)
        owned_combo.grid(row=0, column=1, columnspan=2, sticky="ew", pady=2)

        # Callback per aggiornamento automatico sesso
        self.owned_species_var.trace('w', self._on_species_change)

        ttk.Label(add_form, text="Sesso:").grid(row=1, column=0, sticky="w")
        self.owned_gender_combo = ttk.Combobox(add_form, textvariable=self.owned_gender_var, values=["Maschio", "Femmina", "Genderless"], state="readonly")
        self.owned_gender_combo.grid(row=1, column=1, columnspan=2, sticky="ew", pady=2)

        ttk.Label(add_form, text="IVs:").grid(row=2, column=0, sticky="w")
        owned_iv_frame = ttk.Frame(add_form)
        owned_iv_frame.grid(row=2, column=1, columnspan=2, sticky="ew")
        for i, stat in enumerate(self.stats):
            ttk.Checkbutton(owned_iv_frame, text=stat, variable=self.owned_ivs_vars[stat]).grid(row=i//3, column=i%3, sticky="w")

        ttk.Label(add_form, text="Natura:").grid(row=3, column=0, sticky="w")
        owned_nature_combo = ttk.Combobox(add_form, textvariable=self.owned_nature_var, values=self.natures, state="readonly")
        owned_nature_combo.grid(row=3, column=1, columnspan=2, sticky="ew", pady=2)

        ttk.Button(add_form, text="Aggiungi Pokémon", command=self._add_owned_pokemon).grid(row=4, column=1, sticky="e", pady=10)

        list_frame = ttk.Frame(owned_frame)
        list_frame.grid(row=1, column=0, sticky="nsew", pady=10)
        owned_frame.rowconfigure(1, weight=1)

        self.owned_pokemon_tree = ttk.Treeview(list_frame, columns=("ID", "Specie", "Sesso", "IVs", "Natura"), show="headings", height=10)
        self.owned_pokemon_tree.heading("ID", text="ID")
        self.owned_pokemon_tree.heading("Specie", text="Specie")
        self.owned_pokemon_tree.heading("Sesso", text="Sesso")
        self.owned_pokemon_tree.heading("IVs", text="IVs")
        self.owned_pokemon_tree.heading("Natura", text="Natura")
        self.owned_pokemon_tree.column("ID", width=0, stretch=tk.NO)
        self.owned_pokemon_tree.column("Specie", width=100)
        self.owned_pokemon_tree.column("Sesso", width=80)
        self.owned_pokemon_tree.column("IVs", width=200)
        self.owned_pokemon_tree.column("Natura", width=100)

        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.owned_pokemon_tree.yview)
        self.owned_pokemon_tree.configure(yscrollcommand=scrollbar.set)

        self.owned_pokemon_tree.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)

        ttk.Button(owned_frame, text="Rimuovi Selezionato", command=self._remove_owned_pokemon).grid(row=2, column=0, sticky="e", pady=5)

    def _create_actions_section(self, parent):
        actions_frame = ttk.Frame(parent, padding="10")
        actions_frame.grid(row=2, column=0, sticky="ew")
        actions_frame.columnconfigure(0, weight=1)
        actions_frame.columnconfigure(1, weight=1)

        ttk.Button(actions_frame, text="Genera e Valuta Piani", command=self._run_evaluation_phase_1).grid(row=0, column=0, padx=5, sticky="ew")
        ttk.Button(actions_frame, text="Reset", command=self._reset_all).grid(row=0, column=1, padx=5, sticky="ew")

    def _create_results_section(self, parent):
        results_notebook = ttk.Notebook(parent)
        results_notebook.grid(row=0, column=0, sticky="nsew")
        parent.rowconfigure(0, weight=1)
        parent.columnconfigure(0, weight=1)

        tree_frame = ttk.Frame(results_notebook, padding="5")
        results_notebook.add(tree_frame, text="Albero Genealogico")
        tree_frame.rowconfigure(0, weight=1)
        tree_frame.columnconfigure(0, weight=1)

        self.results_canvas = tk.Canvas(tree_frame, bg="white")
        h_scroll = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.results_canvas.xview)
        v_scroll = ttk.Scrollbar(tree_frame, orient="vertical", command=self.results_canvas.yview)
        self.results_canvas.configure(xscrollcommand=h_scroll.set, yscrollcommand=v_scroll.set)
        self.results_canvas.grid(row=0, column=0, sticky="nsew")
        h_scroll.grid(row=1, column=0, sticky="ew")
        v_scroll.grid(row=0, column=1, sticky="ns")

        text_frame = ttk.Frame(results_notebook, padding="5")
        results_notebook.add(text_frame, text="Piano Testuale")
        text_frame.rowconfigure(0, weight=1)
        text_frame.columnconfigure(0, weight=1)

        self.results_text = tk.Text(text_frame, wrap="word", height=20, width=80, state="disabled", font=("Courier New", 10))
        text_scroll = ttk.Scrollbar(text_frame, orient="vertical", command=self.results_text.yview)
        self.results_text.configure(yscrollcommand=text_scroll.set)
        self.results_text.grid(row=0, column=0, sticky="nsew")
        text_scroll.grid(row=0, column=1, sticky="ns")

    def _add_owned_pokemon(self):
        specie = self.owned_species_var.get()
        if not specie or specie not in self.pokemon_names:
            messagebox.showwarning("Input Invalido", "Seleziona una specie valida per il Pokémon.")
            return

        ivs = [stat for stat, var in self.owned_ivs_vars.items() if var.get()]
        natura = self.owned_nature_var.get()
        if natura == "Nessuna":
            natura = None

        sesso = self.owned_gender_var.get()

        pokemon_id = str(uuid.uuid4())
        new_pokemon = PokemonPosseduto(id_utente=pokemon_id, specie=specie, ivs=ivs, natura=natura, sesso=sesso)
        self.owned_pokemon_list.append(new_pokemon)

        iv_str = ", ".join(ivs) if ivs else "Nessuno"
        natura_str = natura if natura else "Nessuna"
        self.owned_pokemon_tree.insert("", "end", iid=pokemon_id, values=(pokemon_id, specie, sesso, iv_str, natura_str))

        self.owned_species_var.set("")
        for var in self.owned_ivs_vars.values():
            var.set(False)
        self.owned_nature_var.set("Nessuna")
        # Reset sesso
        self.owned_gender_combo.config(state="readonly")
        self.owned_gender_var.set("Maschio")

    def _on_species_change(self, *args):
        specie = self.owned_species_var.get()
        if specie in self.gender_data:
            gender_type = self.gender_data[specie].get("gender_type", "").lower()

            if "solo maschio" in gender_type:
                self.owned_gender_var.set("Maschio")
                self.owned_gender_combo.config(state="disabled")
            elif "solo femmina" in gender_type:
                self.owned_gender_var.set("Femmina")
                self.owned_gender_combo.config(state="disabled")
            elif "genderless" in gender_type:
                self.owned_gender_var.set("Genderless")
                self.owned_gender_combo.config(state="disabled")
            else:
                self.owned_gender_combo.config(state="readonly")
                # Se era bloccato su un valore, sbloccalo ma non cambiare valore a meno che non sia invalido
                curr = self.owned_gender_var.get()
                if curr not in ["Maschio", "Femmina"]:
                    self.owned_gender_var.set("Maschio")
        else:
            self.owned_gender_combo.config(state="readonly")

    def _remove_owned_pokemon(self):
        selected_items = self.owned_pokemon_tree.selection()
        if not selected_items:
            messagebox.showwarning("Nessuna Selezione", "Seleziona un Pokémon dalla lista per rimuoverlo.")
            return
        for item_id in selected_items:
            self.owned_pokemon_list = [p for p in self.owned_pokemon_list if p.id_utente != item_id]
            self.owned_pokemon_tree.delete(item_id)

    def _run_evaluation_phase_1(self):
        """Generates plans and selects candidates, then opens price dialog."""
        self._log_state("START_EVALUATION")
        target_ivs = [stat for stat, var in self.target_ivs_vars.items() if var.get()]
        target_nature = self.target_nature_var.get()
        if target_nature == "Nessuna":
            target_nature = None

        target_species = self.target_species_var.get()
        if not target_species or target_species not in self.pokemon_names:
             messagebox.showerror("Errore Target", "Seleziona una specie valida per il Pokémon target.")
             return
        if len(target_ivs) < 2:
            messagebox.showerror("Errore Target", "Seleziona almeno 2 IVs per il Pokémon target.")
            return

        self._clear_results()
        self.results_canvas.create_text(300, 100, text=f"Generazione piani per {len(target_ivs)}IV in corso...", font=("Arial", 12))
        self.update_idletasks()

        try:
            piani_generati = core_engine.esegui_generazione(target_ivs, target_nature)
        except Exception as e:
            messagebox.showerror("Errore Engine", f"Si è verificato un errore durante la generazione dei piani:\n{e}")
            self._clear_results()
            return

        if not piani_generati:
            messagebox.showinfo("Nessun Piano", f"Nessun piano trovato.")
            self._clear_results()
            return

        # Initial Evaluation (Score Only)
        try:
            piani_valutati = plan_evaluator.valuta_piani(
                piani_generati, 
                self.owned_pokemon_list, 
                target_species, 
                self.pokemon_data, 
                self.gender_data
            )
        except Exception as e:
            messagebox.showerror("Errore Valutatore", f"Si è verificato un errore:\n{e}")
            self._clear_results()
            return

        # Keep Top candidates (e.g. Top 20)
        self.generated_plans_cache = piani_valutati[:20]

        # Analyze Ingredients for Price Dialog
        required_stats = set()

        # Helper to traverse plan and find holes
        def find_holes(plan_val):
            holes = set()
            piano = plan_val.piano_originale
            mappa = plan_val.mappa_assegnazioni

            # Map nodes
            node_map = {}
            child_to_parents = {}
            for l in piano.livelli:
                for acc in l.accoppiamenti:
                    node_map[id(acc.genitore1)] = acc.genitore1
                    node_map[id(acc.genitore2)] = acc.genitore2
                    node_map[id(acc.figlio)] = acc.figlio
                    child_to_parents[id(acc.figlio)] = (id(acc.genitore1), id(acc.genitore2))

            def traverse(node_id):
                if node_id in mappa:
                    return # Owned

                # Check if leaf
                if node_id not in child_to_parents:
                    # Is a hole
                    node = node_map[node_id]
                    # Get stats
                    for r in node.ruoli_iv:
                        stat = piano.legenda_ruoli.get(r)
                        if stat: holes.add(stat)
                    if node.ruolo_natura:
                        n = piano.legenda_ruoli.get(node.ruolo_natura)
                        if n: holes.add("Natura")
                else:
                    p1, p2 = child_to_parents[node_id]
                    traverse(p1)
                    traverse(p2)

            # Start from root
            final_node = piano.livelli[-1].accoppiamenti[0].figlio
            traverse(id(final_node))
            return holes

        for p in self.generated_plans_cache:
            required_stats.update(find_holes(p))

        if not required_stats:
            # No holes! All owned. Just show result.
            self._display_plan(self.generated_plans_cache[0])
            return

        # Extract Relevant Egg Groups
        relevant_groups = self.pokemon_data.get(target_species, [])

        # Open Dialog
        PriceInputDialog(
            self,
            required_stats,
            self.price_manager,
            self._run_evaluation_phase_2,
            relevant_egg_groups=relevant_groups,
            target_species=target_species,
            target_nature=target_nature,
            pokemon_data=self.pokemon_data,
            gender_data=self.gender_data
        )

    def _run_evaluation_phase_2(self, price_manager_override=None):
        """Calculates costs using entered prices and shows best result."""
        target_species = self.target_species_var.get()
        target_nature = self.target_nature_var.get()
        if target_nature == "Nessuna": target_nature = None

        # Use the override if provided (from Popup), otherwise use the main one (shouldn't happen in normal flow but safe fallback)
        pm_to_use = price_manager_override if price_manager_override else self.price_manager

        # Re-evaluate cost for cached plans
        for p_val in self.generated_plans_cache:
            ev = plan_evaluator.PlanEvaluator(
                p_val.piano_originale,
                self.owned_pokemon_list,
                pm_to_use,
                target_species,
                self.pokemon_data,
                target_nature,
                self.gender_data # Pass Gender Data
            )
            ev._build_tree_maps()
            ev._identify_mandatory_nodes() # Important for cost calculation context
            ev.update_cost(p_val)

        # Sort: Primary Cost (Asc), Secondary Score (Desc)
        self.generated_plans_cache.sort(key=lambda p: p.punteggio, reverse=True) # Ensure score priority
        self.generated_plans_cache.sort(key=lambda p: p.costo_totale) # Then sort by cost (Cheapest first)

        best = self.generated_plans_cache[0]
        self._display_plan(best)

    def _display_plan(self, piano_valutato: PianoValutato):
        self._clear_results()
        try:
            self._display_tree_plan(piano_valutato)
        except Exception as e:
            print(f"Errore visualizzazione albero: {e}")

        try:
            self._display_text_plan(piano_valutato)
        except Exception as e:
            print(f"Errore visualizzazione testo: {e}")
            self.results_text.config(state="normal")
            self.results_text.insert("1.0", f"Errore durante la generazione del report testuale:\n{e}")
            self.results_text.config(state="disabled")

    def _display_text_plan(self, piano_valutato: PianoValutato):
        self.results_text.config(state="normal")
        self.results_text.delete("1.0", tk.END) # Safety clear

        piano = piano_valutato.piano_originale
        legenda = piano.legenda_ruoli
        costo = piano_valutato.costo_totale

        output = []
        output.append(f"--- PIANO DI BREEDING OTTIMALE (Punteggio: {piano_valutato.punteggio:.2f}) ---\n")

        cost_str = f"{costo:,}".replace(",", ".")
        if costo >= 999999990: cost_str = "NON CALCOLABILE (O > 999M)"

        output.append(f"COSTO TOTALE STIMATO: ${cost_str}\n")
        output.append("Legenda Statistiche:\n")
        for ruolo, stat in legenda.items():
            output.append(f"  - {ruolo}: {stat}\n")
        output.append("\n" + "="*60 + "\n")

        owned_map = {p.id_utente: p for p in self.owned_pokemon_list}

        for livello in piano.livelli:
            # Filtra gli accoppiamenti il cui risultato è già posseduto (non serve mostrare come crearlo)
            active_couplings = [acc for acc in livello.accoppiamenti if id(acc.figlio) not in piano_valutato.mappa_assegnazioni]

            if not active_couplings:
                continue

            output.append(f"\n--- Livello {livello.livello_id} ---\n")
            for acc in active_couplings:
                gen1_str = self._get_node_text(acc.genitore1, piano.legenda_ruoli, piano_valutato, owned_map).replace('\n', ' ')
                gen2_str = self._get_node_text(acc.genitore2, piano.legenda_ruoli, piano_valutato, owned_map).replace('\n', ' ')
                figlio_str = self._get_node_text(acc.figlio, piano.legenda_ruoli, piano_valutato, owned_map).replace('\n', ' ')

                output.append(f"  {gen1_str:<45} + {gen2_str:<45} -> {figlio_str}\n")

        self.results_text.insert("1.0", "".join(output))
        
        # Log the final text plan
        try:
            logging.info("FINAL TEXT PLAN GENERATED:\n" + "".join(output))
        except Exception as e:
            logging.error(f"Failed to log text plan: {e}")

        self.results_text.config(state="disabled")

    def _display_tree_plan(self, piano_valutato: PianoValutato):
        self.update_idletasks()
        piano = piano_valutato.piano_originale
        assegnazioni = piano_valutato.mappa_assegnazioni
        owned_pokemon_map = {p.id_utente: p for p in self.owned_pokemon_list}

        child_to_parents_map = {}
        for livello in piano.livelli:
            for acc in livello.accoppiamenti:
                child_id = id(acc.figlio)
                child_to_parents_map[child_id] = (acc.genitore1, acc.genitore2)

        final_target = piano.livelli[-1].accoppiamenti[0].figlio
        self.node_widths = {}
        self._calculate_node_widths(final_target, child_to_parents_map, assegnazioni)

        total_width = self.node_widths.get(id(final_target), 120)
        start_x = total_width / 2 + 50

        self._draw_node(final_target, start_x, 50, child_to_parents_map, piano_valutato, owned_pokemon_map, piano.legenda_ruoli)

        bbox = self.results_canvas.bbox("all")
        if bbox:
            self.results_canvas.config(scrollregion=(0, 0, total_width + 100, bbox[3] + 50))

    def _get_node_text(self, node, legenda, piano_valutato, owned_map):
        node_id = id(node)

        # Check Owned
        if node_id in piano_valutato.mappa_assegnazioni:
            user_id = piano_valutato.mappa_assegnazioni[node_id]
            posseduto = owned_map.get(user_id)
            if posseduto:
                iv_str = ", ".join(posseduto.ivs)
                natura_str = f"\n+ {posseduto.natura}" if posseduto.natura else ""
                return f"✔ Usa tuo {posseduto.specie}\n[{iv_str}]{natura_str}"
            else:
                return f"✔ Usa tuo Pokemon (ID Non Trovato)"

        # Check Purchased
        if node_id in piano_valutato.mappa_acquisti:
            return f"🛒 {piano_valutato.mappa_acquisti[node_id]}"

        # Standard Description
        iv_names = sorted([legenda.get(r, r) for r in node.ruoli_iv])
        natura_name = legenda.get(node.ruolo_natura)
        iv_str = ", ".join(iv_names)
        if len(iv_str) > 18:
            parts = iv_str.split(", ")
            mid = (len(parts) + 1) // 2
            iv_str = ", ".join(parts[:mid]) + ",\n" + ", ".join(parts[mid:])
        if natura_name:
            return f"{iv_str}\n+ {natura_name}"
        else:
            return f"{iv_str}\n[{len(iv_names)}IV]"

    def _calculate_node_widths(self, node, child_to_parents_map, assegnazioni):
        node_id = id(node)
        node_width = 120
        h_spacing = 30
        is_owned = node_id in assegnazioni
        if is_owned or node_id not in child_to_parents_map:
            self.node_widths[node_id] = node_width
            return node_width
        if node_id in self.node_widths:
            return self.node_widths[node_id]
        genitore1, genitore2 = child_to_parents_map[node_id]
        width1 = self._calculate_node_widths(genitore1, child_to_parents_map, assegnazioni)
        width2 = self._calculate_node_widths(genitore2, child_to_parents_map, assegnazioni)
        total_width = width1 + width2 + h_spacing
        self.node_widths[node_id] = total_width
        return total_width

    def _draw_node(self, node, x, y, child_to_parents_map, piano_valutato, owned_map, legenda):
        node_id = id(node)
        node_width, node_height = 120, 50
        v_spacing = 90
        h_spacing = 30
        is_owned = node_id in piano_valutato.mappa_assegnazioni
        is_bought = node_id in piano_valutato.mappa_acquisti

        fill_color = "#ADD8E6"
        outline_color = "#00008B"

        if is_owned:
            fill_color = "#90EE90"
            outline_color = "#006400"
        elif is_bought:
            fill_color = "#FFD700" # Gold for bought
            outline_color = "#B8860B"

        self.results_canvas.create_rectangle(x - node_width/2, y - node_height/2, x + node_width/2, y + node_height/2, fill=fill_color, outline=outline_color, width=2)
        text = self._get_node_text(node, legenda, piano_valutato, owned_map)
        self.results_canvas.create_text(x, y, text=text, font=("Arial", 8, "bold" if is_owned else "normal"), justify=tk.CENTER)

        if not is_owned and node_id in child_to_parents_map:
            genitore1, genitore2 = child_to_parents_map[node_id]
            width1 = self.node_widths.get(id(genitore1), node_width)
            width2 = self.node_widths.get(id(genitore2), node_width)
            new_y = y + v_spacing
            start_x1 = x - (width1 + width2 + h_spacing) / 2
            x1 = start_x1 + width1 / 2
            x2 = start_x1 + width1 + h_spacing + width2 / 2
            self.results_canvas.create_line(x, y + node_height/2, x1, new_y - node_height/2, width=1.5)
            self.results_canvas.create_line(x, y + node_height/2, x2, new_y - node_height/2, width=1.5)
            self._draw_node(genitore1, x1, new_y, child_to_parents_map, piano_valutato, owned_map, legenda)
            self._draw_node(genitore2, x2, new_y, child_to_parents_map, piano_valutato, owned_map, legenda)

    def _clear_results(self):
        self.results_canvas.delete("all")
        self.results_text.config(state="normal")
        self.results_text.delete("1.0", tk.END)
        self.results_text.config(state="disabled")

    def _reset_all(self):
        self.target_species_var.set("")
        for var in self.target_ivs_vars.values():
            var.set(False)
        self.target_nature_var.set("Nessuna")
        self.owned_species_var.set("")
        for var in self.owned_ivs_vars.values():
            var.set(False)
        self.owned_nature_var.set("Nessuna")
        for item in self.owned_pokemon_tree.get_children():
            self.owned_pokemon_tree.delete(item)
        self.owned_pokemon_list.clear()
        self._clear_results()
        messagebox.showinfo("Reset", "Tutti i campi sono stati resettati.")

if __name__ == '__main__':
    app = BreedingToolApp()
    app.mainloop()
