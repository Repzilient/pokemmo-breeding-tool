import tkinter as tk
from tkinter import ttk, messagebox
import json
import uuid
from typing import Set, List

# Importa le classi e le funzioni necessarie dai file del progetto
from structures import PokemonPosseduto, PokemonRichiesto, PianoValutato
import core_engine
import plan_evaluator
from price_manager import PriceManager
from gender_helper import GenderHelper


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
        for element in self._completion_list:
            if element.lower().startswith(self.get().lower()):
                _hits.append(element)

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
    """
    def __init__(self, parent, required_stats: Set[str], price_manager: PriceManager, on_confirm):
        super().__init__(parent)
        self.title("Inserimento Prezzi di Mercato")
        self.geometry("900x600")
        self.price_manager = price_manager
        self.on_confirm = on_confirm
        self.required_stats = sorted(list(required_stats))
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

        # Headers
        headers = ["Statistica / Natura", "Specie (M)", "Specie (F)", "EggGroup (M)", "EggGroup (F)", "Ditto"]
        for col, text in enumerate(headers):
            ttk.Label(scrollable_frame, text=text, font=("Arial", 10, "bold")).grid(row=0, column=col, padx=5, pady=5)

        # Rows
        for i, stat in enumerate(self.required_stats):
            row = i + 1
            ttk.Label(scrollable_frame, text=stat).grid(row=row, column=0, padx=5, pady=5, sticky="w")

            self.inputs[stat] = {}

            # Specie M
            sm = ttk.Entry(scrollable_frame, width=10)
            sm.grid(row=row, column=1, padx=2)
            self.inputs[stat]["Specie_M"] = sm

            # Specie F
            sf = ttk.Entry(scrollable_frame, width=10)
            sf.grid(row=row, column=2, padx=2)
            self.inputs[stat]["Specie_F"] = sf

            # EggGroup M
            em = ttk.Entry(scrollable_frame, width=10)
            em.grid(row=row, column=3, padx=2)
            self.inputs[stat]["EggGroup_M"] = em

            # EggGroup F
            ef = ttk.Entry(scrollable_frame, width=10)
            ef.grid(row=row, column=4, padx=2)
            self.inputs[stat]["EggGroup_F"] = ef

            # Ditto
            d = ttk.Entry(scrollable_frame, width=10)
            d.grid(row=row, column=5, padx=2)
            self.inputs[stat]["Ditto"] = d

        # Button Frame
        btn_frame = ttk.Frame(container)
        btn_frame.pack(pady=20)

        # Confirm Button
        ttk.Button(btn_frame, text="Calcola Costi e Valuta", command=self._confirm).pack(side="left", padx=10)

        # Skip Prices Button
        ttk.Button(btn_frame, text="Non aggiungere prezzi", command=self._skip_prices).pack(side="left", padx=10)

    def _confirm(self):
        self.price_manager.clear()

        for stat, entries in self.inputs.items():
            try:
                # Helper to parse int or default to infinity
                def get_val(entry):
                    val = entry.get().strip()
                    if not val: return 999999999
                    return int(val)

                self.price_manager.set_price(stat, "Specie", "M", get_val(entries["Specie_M"]))
                self.price_manager.set_price(stat, "Specie", "F", get_val(entries["Specie_F"]))
                self.price_manager.set_price(stat, "EggGroup", "M", get_val(entries["EggGroup_M"]))
                self.price_manager.set_price(stat, "EggGroup", "F", get_val(entries["EggGroup_F"]))
                self.price_manager.set_price(stat, "Ditto", "X", get_val(entries["Ditto"]))

            except ValueError:
                messagebox.showerror("Errore", f"Inserisci valori numerici validi per {stat}")
                return

        self.on_confirm()
        self.destroy()

    def _skip_prices(self):
        """Sets all prices to 0 and confirms."""
        self.price_manager.clear()
        for stat in self.required_stats:
            self.price_manager.set_price(stat, "Specie", "M", 0)
            self.price_manager.set_price(stat, "Specie", "F", 0)
            self.price_manager.set_price(stat, "EggGroup", "M", 0)
            self.price_manager.set_price(stat, "EggGroup", "F", 0)
            self.price_manager.set_price(stat, "Ditto", "X", 0)

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
        self._load_pokemon_data()

        self.price_manager = PriceManager()
        self.gender_helper = GenderHelper()

        # --- Variabili di stato ---
        self.owned_pokemon_list = []
        self.target_ivs_vars = {stat: tk.BooleanVar() for stat in self.stats}
        self.owned_ivs_vars = {stat: tk.BooleanVar() for stat in self.stats}
        self.target_nature_var = tk.StringVar(value=self.natures[0])
        self.owned_nature_var = tk.StringVar(value=self.natures[0])
        self.target_species_var = tk.StringVar()
        self.owned_species_var = tk.StringVar()
        self.owned_gender_var = tk.StringVar(value="M")

        # Stored generated plans for phase 2
        self.generated_plans_cache = []

        # --- Creazione dell'interfaccia ---
        self._create_widgets()

    def _load_pokemon_data(self):
        try:
            with open('pokemon_data.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.pokemon_data = data
                self.pokemon_names = sorted(data.keys())
        except FileNotFoundError:
            messagebox.showerror("Errore", "File 'pokemon_data.json' non trovato.")
            self.destroy()
        except json.JSONDecodeError:
            messagebox.showerror("Errore", "Il file 'pokemon_data.json' non è formattato correttamente.")
            self.destroy()

    def _create_widgets(self):
        main_frame = ttk.Frame(self, padding="10")
        main_frame.grid(row=0, column=0, sticky="nsew")
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        left_frame = ttk.Frame(main_frame, padding="10")
        left_frame.grid(row=0, column=0, sticky="ns", padx=(0, 10))
        main_frame.columnconfigure(0, weight=1)

        right_frame = ttk.Frame(main_frame, padding="10")
        right_frame.grid(row=0, column=1, sticky="nsew")
        main_frame.columnconfigure(1, weight=3)
        main_frame.rowconfigure(0, weight=1)

        self._create_target_section(left_frame)
        self._create_owned_section(left_frame)
        self._create_actions_section(left_frame)
        self._create_results_section(right_frame)

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
        self.owned_combo = AutocompleteCombobox(add_form, textvariable=self.owned_species_var)
        self.owned_combo.set_completion_list(self.pokemon_names)
        self.owned_combo.grid(row=0, column=1, columnspan=2, sticky="ew", pady=2)
        # Bind event for gender update
        self.owned_combo.bind("<<ComboboxSelected>>", self._on_owned_species_selected)
        self.owned_combo.bind("<FocusOut>", self._on_owned_species_selected)

        ttk.Label(add_form, text="Sesso:").grid(row=0, column=3, sticky="w", padx=(10, 5))
        self.gender_combo = ttk.Combobox(add_form, textvariable=self.owned_gender_var, values=["M", "F", "Genderless"], state="readonly", width=10)
        self.gender_combo.grid(row=0, column=4, sticky="ew", pady=2)

        ttk.Label(add_form, text="IVs:").grid(row=1, column=0, sticky="w")
        owned_iv_frame = ttk.Frame(add_form)
        owned_iv_frame.grid(row=1, column=1, columnspan=4, sticky="ew")
        for i, stat in enumerate(self.stats):
            ttk.Checkbutton(owned_iv_frame, text=stat, variable=self.owned_ivs_vars[stat]).grid(row=i//3, column=i%3, sticky="w")

        ttk.Label(add_form, text="Natura:").grid(row=2, column=0, sticky="w")
        owned_nature_combo = ttk.Combobox(add_form, textvariable=self.owned_nature_var, values=self.natures, state="readonly")
        owned_nature_combo.grid(row=2, column=1, columnspan=2, sticky="ew", pady=2)

        ttk.Button(add_form, text="Aggiungi Pokémon", command=self._add_owned_pokemon).grid(row=3, column=4, sticky="e", pady=10)

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
        self.owned_pokemon_tree.column("Sesso", width=50)
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

    def _on_owned_species_selected(self, event=None):
        specie = self.owned_species_var.get().strip()
        if not specie:
            return

        # Query Gender Helper
        ratio_type = self.gender_helper.get_gender_ratio_type(specie)

        # Adjust Combo
        if "solo maschio" in ratio_type:
            self.gender_combo.set("M")
            self.gender_combo.state(["disabled"])
        elif "solo femmina" in ratio_type:
            self.gender_combo.set("F")
            self.gender_combo.state(["disabled"])
        elif "genderless" in ratio_type:
            self.gender_combo.set("Genderless")
            self.gender_combo.state(["disabled"])
        else:
            # maschio e femmina, or N/A
            self.gender_combo.state(["!disabled"])
            if self.gender_combo.get() not in ["M", "F"]:
                self.gender_combo.set("M") # Default

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
        self.gender_combo.state(["!disabled"])
        self.gender_combo.set("M")
        for var in self.owned_ivs_vars.values():
            var.set(False)
        self.owned_nature_var.set("Nessuna")

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
            piani_valutati = plan_evaluator.valuta_piani(piani_generati, self.owned_pokemon_list)
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

        # Open Dialog
        PriceInputDialog(self, required_stats, self.price_manager, self._run_evaluation_phase_2)

    def _run_evaluation_phase_2(self):
        """Calculates costs using entered prices and shows best result."""
        target_species = self.target_species_var.get()
        target_nature = self.target_nature_var.get()
        if target_nature == "Nessuna": target_nature = None

        # Re-evaluate cost for cached plans
        for p_val in self.generated_plans_cache:
            ev = plan_evaluator.PlanEvaluator(
                p_val.piano_originale,
                self.owned_pokemon_list,
                self.price_manager,
                target_species,
                self.pokemon_data,
                target_nature,
                self.gender_helper
            )
            ev._build_tree_maps()
            ev.update_cost(p_val)

        # Sort: Primary Cost (Asc), Secondary Score (Desc)
        self.generated_plans_cache.sort(key=lambda p: p.punteggio, reverse=True) # Ensure score priority
        self.generated_plans_cache.sort(key=lambda p: p.costo_totale) # Then sort by cost (Cheapest first)

        best = self.generated_plans_cache[0]
        self._display_plan(best)

    def _display_plan(self, piano_valutato: PianoValutato):
        self._clear_results()
        self._display_tree_plan(piano_valutato)
        self._display_text_plan(piano_valutato)

    def _display_text_plan(self, piano_valutato: PianoValutato):
        self.results_text.config(state="normal")
        piano = piano_valutato.piano_originale
        legenda = piano.legenda_ruoli
        costo = piano_valutato.costo_totale

        output = []
        output.append(f"--- PIANO DI BREEDING OTTIMALE (Punteggio: {piano_valutato.punteggio:.2f}) ---\n")

        cost_str = f"{costo:,}".replace(",", ".")
        if costo >= 999999: cost_str = "NON CALCOLABILE"

        output.append(f"COSTO TOTALE STIMATO: ${cost_str}\n")
        output.append("Legenda Statistiche:\n")
        for ruolo, stat in legenda.items():
            output.append(f"  - {ruolo}: {stat}\n")
        output.append("\n" + "="*60 + "\n")

        for livello in piano.livelli:
            output.append(f"\n--- Livello {livello.livello_id} ---\n")
            for acc in livello.accoppiamenti:
                gen1_str = self._get_node_text(acc.genitore1, piano.legenda_ruoli, piano_valutato, {p.id_utente: p for p in self.owned_pokemon_list}).replace('\n', ' ')
                gen2_str = self._get_node_text(acc.genitore2, piano.legenda_ruoli, piano_valutato, {p.id_utente: p for p in self.owned_pokemon_list}).replace('\n', ' ')
                figlio_str = self._get_node_text(acc.figlio, piano.legenda_ruoli, piano_valutato, {}).replace('\n', ' ')

                output.append(f"  {gen1_str:<45} + {gen2_str:<45} -> {figlio_str}\n")

        self.results_text.insert("1.0", "".join(output))
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
            posseduto = owned_map[piano_valutato.mappa_assegnazioni[node_id]]
            iv_str = ", ".join(posseduto.ivs)
            natura_str = f"\n+ {posseduto.natura}" if posseduto.natura else ""
            return f"✔ Usa tuo {posseduto.specie}\n[{iv_str}]{natura_str}"

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
