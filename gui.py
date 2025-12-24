import tkinter as tk
from tkinter import ttk, messagebox
import json
import uuid

# Importa le classi e le funzioni necessarie dai file del progetto
from structures import PokemonPosseduto, PokemonRichiesto
import core_engine
import plan_evaluator


# --- Classe AutocompleteCombobox ---
# Basata sulla soluzione di Mitja Martini e Russell Adams, adattata da ttkwidgets.
# Fonte: https://mail.python.org/pipermail/tkinter-discuss/2012-January/003041.html
class AutocompleteCombobox(ttk.Combobox):
    """
    Un ttk.Combobox con funzionalità di autocompletamento.
    Gestisce la selezione, il completamento del testo e la navigazione
    in modo robusto.
    """
    def set_completion_list(self, completion_list):
        """Imposta la lista di valori per l'autocompletamento."""
        self._completion_list = sorted(completion_list, key=str.lower)
        self._hits = []
        self._hit_index = 0
        self.position = 0
        self.bind('<KeyRelease>', self.handle_keyrelease)
        self['values'] = self._completion_list

    def autocomplete(self, delta=0):
        """
        Esegue l'autocompletamento e scorre tra i suggerimenti.
        delta: 0 per il primo suggerimento, 1 per il successivo, -1 per il precedente.
        """
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
        """Gestisce l'evento di rilascio di un tasto in modo intelligente."""

        if event.keysym in ("Up", "Down"):
            self.autocomplete(delta=1 if event.keysym == "Down" else -1)
            return

        if event.keysym == "BackSpace":
            self.delete(self.index(tk.INSERT) -1, tk.END)
            self.position = self.index(tk.END)

        if len(event.keysym) == 1:
            self.autocomplete()


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
        self.natures = [
            "Nessuna", "Adamant", "Modest", "Jolly", "Timid", "Bold", "Calm",
            "Impish", "Careful", "Brave", "Quiet", "Rash", "Mild", "Hasty",
            "Serious", "Docile", "Hardy", "Bashful", "Quirky", "Lonely",
            "Naughty", "Gentle", "Lax", "Relaxed", "Sassy"
        ]
        self.stats = ["PS", "Attacco", "Difesa", "Attacco Speciale", "Difesa Speciale", "Velocità"]
        self._load_pokemon_data()

        # --- Variabili di stato ---
        self.owned_pokemon_list = []
        self.target_ivs_vars = {stat: tk.BooleanVar() for stat in self.stats}
        self.owned_ivs_vars = {stat: tk.BooleanVar() for stat in self.stats}
        self.target_nature_var = tk.StringVar(value=self.natures[0])
        self.owned_nature_var = tk.StringVar(value=self.natures[0])
        self.target_species_var = tk.StringVar()
        self.owned_species_var = tk.StringVar()

        # --- Creazione dell'interfaccia ---
        self._create_widgets()

    def _load_pokemon_data(self):
        """Carica i nomi dei Pokémon dal file JSON."""
        try:
            with open('pokemon_data.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.pokemon_names = sorted(data.keys())
        except FileNotFoundError:
            messagebox.showerror("Errore", "File 'pokemon_data.json' non trovato. Assicurati che sia nella stessa cartella.")
            self.destroy()
        except json.JSONDecodeError:
            messagebox.showerror("Errore", "Il file 'pokemon_data.json' non è formattato correttamente.")
            self.destroy()

    def _create_widgets(self):
        """Crea e organizza tutti i widget dell'interfaccia."""
        main_frame = ttk.Frame(self, padding="10")
        main_frame.grid(row=0, column=0, sticky="nsew")
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        # --- Frame Sinistro: Input ---
        left_frame = ttk.Frame(main_frame, padding="10")
        left_frame.grid(row=0, column=0, sticky="ns", padx=(0, 10))
        main_frame.columnconfigure(0, weight=1)

        # --- Frame Destro: Risultati ---
        right_frame = ttk.Frame(main_frame, padding="10")
        right_frame.grid(row=0, column=1, sticky="nsew")
        main_frame.columnconfigure(1, weight=3)
        main_frame.rowconfigure(0, weight=1)

        # --- Sezione Pokémon Target ---
        self._create_target_section(left_frame)

        # --- Sezione Pokémon Posseduti ---
        self._create_owned_section(left_frame)

        # --- Sezione Azioni ---
        self._create_actions_section(left_frame)

        # --- Sezione Risultati ---
        self._create_results_section(right_frame)

    def _create_target_section(self, parent):
        """Crea la sezione per definire il Pokémon target."""
        target_frame = ttk.LabelFrame(parent, text="Pokémon Target", padding="10")
        target_frame.grid(row=0, column=0, sticky="ew", pady=5)
        target_frame.columnconfigure(1, weight=1)

        # Specie
        ttk.Label(target_frame, text="Specie:").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        target_combo = AutocompleteCombobox(target_frame, textvariable=self.target_species_var)
        target_combo.set_completion_list(self.pokemon_names)
        target_combo.grid(row=0, column=1, sticky="ew", padx=5, pady=2)

        # IVs
        ttk.Label(target_frame, text="IVs Desiderate:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        iv_frame = ttk.Frame(target_frame)
        iv_frame.grid(row=1, column=1, sticky="ew")
        for i, stat in enumerate(self.stats):
            ttk.Checkbutton(iv_frame, text=stat, variable=self.target_ivs_vars[stat]).grid(row=i//3, column=i%3, sticky="w", padx=5)

        # Natura
        ttk.Label(target_frame, text="Natura:").grid(row=2, column=0, sticky="w", padx=5, pady=2)
        nature_combo = ttk.Combobox(target_frame, textvariable=self.target_nature_var, values=self.natures, state="readonly")
        nature_combo.grid(row=2, column=1, sticky="ew", padx=5, pady=2)

    def _create_owned_section(self, parent):
        """Crea la sezione per aggiungere e visualizzare i Pokémon posseduti."""
        owned_frame = ttk.LabelFrame(parent, text="Pokémon Posseduti", padding="10")
        owned_frame.grid(row=1, column=0, sticky="ew", pady=5)
        owned_frame.columnconfigure(0, weight=1)

        # --- Form di Aggiunta ---
        add_form = ttk.Frame(owned_frame)
        add_form.grid(row=0, column=0, sticky="ew")
        add_form.columnconfigure(1, weight=1)

        ttk.Label(add_form, text="Specie:").grid(row=0, column=0, sticky="w")
        owned_combo = AutocompleteCombobox(add_form, textvariable=self.owned_species_var)
        owned_combo.set_completion_list(self.pokemon_names)
        owned_combo.grid(row=0, column=1, columnspan=2, sticky="ew", pady=2)

        ttk.Label(add_form, text="IVs:").grid(row=1, column=0, sticky="w")
        owned_iv_frame = ttk.Frame(add_form)
        owned_iv_frame.grid(row=1, column=1, columnspan=2, sticky="ew")
        for i, stat in enumerate(self.stats):
            ttk.Checkbutton(owned_iv_frame, text=stat, variable=self.owned_ivs_vars[stat]).grid(row=i//3, column=i%3, sticky="w")

        ttk.Label(add_form, text="Natura:").grid(row=2, column=0, sticky="w")
        owned_nature_combo = ttk.Combobox(add_form, textvariable=self.owned_nature_var, values=self.natures, state="readonly")
        owned_nature_combo.grid(row=2, column=1, columnspan=2, sticky="ew", pady=2)

        ttk.Button(add_form, text="Aggiungi Pokémon", command=self._add_owned_pokemon).grid(row=3, column=1, sticky="e", pady=10)

        # --- Lista Pokémon Posseduti ---
        list_frame = ttk.Frame(owned_frame)
        list_frame.grid(row=1, column=0, sticky="nsew", pady=10)
        owned_frame.rowconfigure(1, weight=1)

        self.owned_pokemon_tree = ttk.Treeview(list_frame, columns=("ID", "Specie", "IVs", "Natura"), show="headings", height=10)
        self.owned_pokemon_tree.heading("ID", text="ID")
        self.owned_pokemon_tree.heading("Specie", text="Specie")
        self.owned_pokemon_tree.heading("IVs", text="IVs")
        self.owned_pokemon_tree.heading("Natura", text="Natura")
        self.owned_pokemon_tree.column("ID", width=0, stretch=tk.NO) # Nasconde la colonna ID
        self.owned_pokemon_tree.column("Specie", width=100)
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
        """Crea i bottoni per le azioni principali."""
        actions_frame = ttk.Frame(parent, padding="10")
        actions_frame.grid(row=2, column=0, sticky="ew")
        actions_frame.columnconfigure(0, weight=1)
        actions_frame.columnconfigure(1, weight=1)

        ttk.Button(actions_frame, text="Genera e Valuta Piani", command=self._run_evaluation).grid(row=0, column=0, padx=5, sticky="ew")
        ttk.Button(actions_frame, text="Reset", command=self._reset_all).grid(row=0, column=1, padx=5, sticky="ew")

    def _create_results_section(self, parent):
        """Crea la sezione dei risultati con le schede."""
        results_notebook = ttk.Notebook(parent)
        results_notebook.grid(row=0, column=0, sticky="nsew")
        parent.rowconfigure(0, weight=1)
        parent.columnconfigure(0, weight=1)

        # --- Scheda Albero Genealogico ---
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

        # --- Scheda Piano Testuale ---
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
        """Aggiunge un Pokémon alla lista dei posseduti."""
        specie = self.owned_species_var.get()
        if not specie or specie not in self.pokemon_names:
            messagebox.showwarning("Input Invalido", "Seleziona una specie valida per il Pokémon.")
            return

        ivs = [stat for stat, var in self.owned_ivs_vars.items() if var.get()]
        natura = self.owned_nature_var.get()
        if natura == "Nessuna":
            natura = None

        pokemon_id = str(uuid.uuid4())

        new_pokemon = PokemonPosseduto(id_utente=pokemon_id, specie=specie, ivs=ivs, natura=natura)
        self.owned_pokemon_list.append(new_pokemon)

        iv_str = ", ".join(ivs) if ivs else "Nessuno"
        natura_str = natura if natura else "Nessuna"
        self.owned_pokemon_tree.insert("", "end", iid=pokemon_id, values=(pokemon_id, specie, iv_str, natura_str))

        self.owned_species_var.set("")
        for var in self.owned_ivs_vars.values():
            var.set(False)
        self.owned_nature_var.set("Nessuna")

    def _remove_owned_pokemon(self):
        """Rimuove il Pokémon selezionato dalla lista."""
        selected_items = self.owned_pokemon_tree.selection()
        if not selected_items:
            messagebox.showwarning("Nessuna Selezione", "Seleziona un Pokémon dalla lista per rimuoverlo.")
            return

        for item_id in selected_items:
            # L'item_id della treeview è l'id_utente che abbiamo impostato
            self.owned_pokemon_list = [p for p in self.owned_pokemon_list if p.id_utente != item_id]
            self.owned_pokemon_tree.delete(item_id)

    def _run_evaluation(self):
        """Esegue la generazione e la valutazione dei piani."""
        target_ivs = [stat for stat, var in self.target_ivs_vars.items() if var.get()]
        target_nature = self.target_nature_var.get()
        if target_nature == "Nessuna":
            target_nature = None

        if len(target_ivs) < 2:
            messagebox.showerror("Errore Target", "Seleziona almeno 2 IVs per il Pokémon target.")
            return

        self._clear_results()
        self.results_canvas.create_text(300, 100, text=f"Generazione piani per {len(target_ivs)}IV in corso...", font=("Arial", 12))
        self.results_text.config(state="normal")
        self.results_text.insert("1.0", f"Generazione piani per {len(target_ivs)}IV in corso...")
        self.results_text.config(state="disabled")
        self.update_idletasks()

        try:
            piani_generati = core_engine.esegui_generazione(target_ivs, target_nature)
        except Exception as e:
            messagebox.showerror("Errore Engine", f"Si è verificato un errore durante la generazione dei piani:\n{e}")
            self._clear_results()
            return

        if not piani_generati:
            messagebox.showinfo("Nessun Piano", f"Nessun piano di breeding trovato per la configurazione richiesta ({len(target_ivs)}IV).")
            self._clear_results()
            return

        try:
            piani_valutati = plan_evaluator.valuta_piani(piani_generati, self.owned_pokemon_list)
        except Exception as e:
            messagebox.showerror("Errore Valutatore", f"Si è verificato un errore durante la valutazione dei piani:\n{e}")
            self._clear_results()
            return

        best_plan = piani_valutati[0]
        self._display_plan(best_plan)

    def _display_plan(self, piano_valutato: plan_evaluator.PianoValutato):
        """Chiama le funzioni per visualizzare il piano in entrambe le schede."""
        self._clear_results()
        self._display_tree_plan(piano_valutato)
        self._display_text_plan(piano_valutato)

    def _display_text_plan(self, piano_valutato: plan_evaluator.PianoValutato):
        """Formatta e visualizza il piano testuale."""
        self.results_text.config(state="normal")

        piano = piano_valutato.piano_originale
        legenda = piano.legenda_ruoli

        output = []
        output.append(f"--- PIANO DI BREEDING OTTIMALE (Punteggio: {piano_valutato.punteggio:.2f}) ---\n")
        output.append("Legenda Statistiche:\n")
        for ruolo, stat in legenda.items():
            output.append(f"  - {ruolo}: {stat}\n")
        output.append("\n" + "="*60 + "\n")

        for livello in piano.livelli:
            output.append(f"\n--- Livello {livello.livello_id} ---\n")
            for acc in livello.accoppiamenti:
                # Updated lookup to use SlotID
                acc_id = id(acc)
                gen1_slot_id = f"{acc_id}_1"
                gen2_slot_id = f"{acc_id}_2"

                gen1_str = self._get_node_text(acc.genitore1, piano.legenda_ruoli, piano_valutato.mappa_assegnazioni, {p.id_utente: p for p in self.owned_pokemon_list}, gen1_slot_id).replace('\n', ' ')
                gen2_str = self._get_node_text(acc.genitore2, piano.legenda_ruoli, piano_valutato.mappa_assegnazioni, {p.id_utente: p for p in self.owned_pokemon_list}, gen2_slot_id).replace('\n', ' ')
                figlio_str = self._get_node_text(acc.figlio, piano.legenda_ruoli, {}, {}, None).replace('\n', ' ')

                output.append(f"  {gen1_str:<45} + {gen2_str:<45} -> {figlio_str}\n")

        self.results_text.insert("1.0", "".join(output))
        self.results_text.config(state="disabled")

    def _display_tree_plan(self, piano_valutato: plan_evaluator.PianoValutato):
        """Disegna l'albero genealogico del piano di breeding sul canvas."""
        self.update_idletasks()

        piano = piano_valutato.piano_originale
        assegnazioni = piano_valutato.mappa_assegnazioni
        owned_pokemon_map = {p.id_utente: p for p in self.owned_pokemon_list}

        # child_to_parents_map needs to track which SLOT produced the parent?
        # No, child_to_parents_map here maps child_id -> (genitore1, genitore2) OBJECTS.
        # But we also need to pass the Coupling ID down the tree to generate Slot IDs for the parents.

        # We need a map: id(child_obj) -> (acc_id, genitore1, genitore2)
        child_to_coupling_map = {}
        for livello in piano.livelli:
            for acc in livello.accoppiamenti:
                child_id = id(acc.figlio)
                child_to_coupling_map[child_id] = acc

        final_target = piano.livelli[-1].accoppiamenti[0].figlio

        self.node_widths = {}
        self._calculate_node_widths(final_target, child_to_coupling_map, assegnazioni) # Note: this uses simplistic width calc which might need update if we check assignments properly?
        # Width calc uses 'is_owned' or 'not in child_to_parents_map'.
        # is_owned check needs SlotID. But we are at Child level.
        # The child is never "assigned" (it is produced). Assignments are on PARENTS.
        # Wait, if I own the intermediate child, I assign it to the parent slot of the next level.
        # But here we are drawing the tree of OBJECTS.

        # The GUI draws the tree of *Objects*.
        # An object might be assigned in one slot but not another (if reused).
        # But typically intermediate objects are distinct.
        # The assignments are on the INPUTS (parents).

        # When drawing a node, we draw the Object.
        # If this Object is a Parent in some coupling, did we assign a Pokemon to it?
        # But a Node in the tree is just an Object.
        # In the visual tree, a Node has parents.
        # The Node itself is the "Child" of the connections below it.
        # And it is the "Parent" of the connection above it.

        # The assignments are relevant when the Node acts as a Parent.
        # But the tree drawing is top-down (Target -> Parents).
        # When we draw a Node, we want to know if *we have it*.
        # If we have it, we display "Use your X".

        # But we assign it to a specific SLOT.
        # If 'acc' produces 'figlio'. 'figlio' is used in 'parent_acc' as 'genitoreX'.
        # So we need to know the 'parent_acc' and 'side' where this node is used.
        # But the recursive function `_draw_node` receives the `node`.
        # It needs to know which SlotID this `node` corresponds to *in the context of its parent in the tree*.

        # `_draw_node` is called by `_draw_node` (recursive).
        # We can pass `slot_id` to `_draw_node`.

        # Initial call: `final_target`. It is the root. No slot ID (it's the result).

        total_width = self.node_widths.get(id(final_target), 120)
        start_x = total_width / 2 + 50

        # We pass None as slot_id for the root.
        self._draw_node(final_target, start_x, 50, child_to_coupling_map, assegnazioni, owned_pokemon_map, piano.legenda_ruoli, None)

        bbox = self.results_canvas.bbox("all")
        if bbox:
            self.results_canvas.config(scrollregion=(0, 0, total_width + 100, bbox[3] + 50))

    def _get_node_text(self, node, legenda, assegnazioni, owned_map, slot_id):
        """Crea il testo formattato per un nodo, traducendo i ruoli in nomi di statistiche."""
        # Check assignment using SlotID
        if slot_id and slot_id in assegnazioni:
            posseduto = owned_map[assegnazioni[slot_id]]
            iv_str = ", ".join(posseduto.ivs)
            natura_str = f"\n+ {posseduto.natura}" if posseduto.natura else ""
            return f"✔ Usa tuo {posseduto.specie}\n[{iv_str}]{natura_str}"
        else:
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

    def _calculate_node_widths(self, node, child_to_coupling_map, assegnazioni):
        """Passata 1: Calcola ricorsivamente la larghezza necessaria per ogni sotto-albero."""
        node_id = id(node)
        # Note: We can't easily check assignment here without context (slot_id).
        # But width calculation mainly depends on whether we expand children or not.
        # We assume we expand if it has parents (is produced by coupling).
        # UNLESS we have it assigned?
        # But we can be assigned to it in multiple places if reused.
        # Assuming for width calc we just check if it has producers.

        # If we want to collapse the tree when we own the pokemon, we need the slot_id context.
        # But width calc is cached by node_id.
        # If the same node is used in two places (one assigned, one not), it has different widths?
        # Yes.
        # So caching by node_id is WRONG if we support context-sensitive width.
        # But for now let's just assume full expansion or update this later.

        # Ideally, we traverse with context.
        # But `_calculate_node_widths` needs to return width.
        # Let's ignore "stop if owned" optimization for width for now, or just check if it has producers.

        node_width = 120
        h_spacing = 30

        if node_id not in child_to_coupling_map:
             self.node_widths[node_id] = node_width
             return node_width

        # If we have producers, we recurse.
        acc = child_to_coupling_map[node_id]
        genitore1 = acc.genitore1
        genitore2 = acc.genitore2

        width1 = self._calculate_node_widths(genitore1, child_to_coupling_map, assegnazioni)
        width2 = self._calculate_node_widths(genitore2, child_to_coupling_map, assegnazioni)

        total_width = width1 + width2 + h_spacing
        self.node_widths[node_id] = total_width
        return total_width

    def _draw_node(self, node, x, y, child_to_coupling_map, assegnazioni, owned_map, legenda, slot_id):
        """Passata 2: Disegna ricorsivamente il nodo e i suoi figli."""
        node_id = id(node)
        node_width, node_height = 120, 50
        v_spacing = 90
        h_spacing = 30

        # Check if owned using the passed slot_id
        is_owned = slot_id and slot_id in assegnazioni

        # Disegna il riquadro e il testo
        fill_color = "#90EE90" if is_owned else "#ADD8E6"
        outline_color = "#006400" if is_owned else "#00008B"
        self.results_canvas.create_rectangle(x - node_width/2, y - node_height/2, x + node_width/2, y + node_height/2, fill=fill_color, outline=outline_color, width=2)
        text = self._get_node_text(node, legenda, assegnazioni, owned_map, slot_id)
        self.results_canvas.create_text(x, y, text=text, font=("Arial", 8, "bold" if is_owned else "normal"), justify=tk.CENTER)

        # Ricorsione per i genitori (ora disegnati sotto)
        # Stop recursion if we own the pokemon at this slot
        if not is_owned and node_id in child_to_coupling_map:
            acc = child_to_coupling_map[node_id]
            genitore1 = acc.genitore1
            genitore2 = acc.genitore2
            acc_id = id(acc)

            # Generate slot IDs for the parents
            slot_id_1 = f"{acc_id}_1"
            slot_id_2 = f"{acc_id}_2"

            width1 = self.node_widths.get(id(genitore1), node_width)
            width2 = self.node_widths.get(id(genitore2), node_width)

            new_y = y + v_spacing

            start_x1 = x - (width1 + width2 + h_spacing) / 2
            x1 = start_x1 + width1 / 2
            x2 = start_x1 + width1 + h_spacing + width2 / 2

            self.results_canvas.create_line(x, y + node_height/2, x1, new_y - node_height/2, width=1.5)
            self.results_canvas.create_line(x, y + node_height/2, x2, new_y - node_height/2, width=1.5)

            self._draw_node(genitore1, x1, new_y, child_to_coupling_map, assegnazioni, owned_map, legenda, slot_id_1)
            self._draw_node(genitore2, x2, new_y, child_to_coupling_map, assegnazioni, owned_map, legenda, slot_id_2)

    def _clear_results(self):
        """Pulisce il canvas e l'area di testo dei risultati."""
        self.results_canvas.delete("all")
        self.results_text.config(state="normal")
        self.results_text.delete("1.0", tk.END)
        self.results_text.config(state="disabled")

    def _reset_all(self):
        """Resetta tutti gli input e i risultati."""
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
