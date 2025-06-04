import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
import json
import os
import sys
import traceback # Per un debug più dettagliato degli errori
from collections import Counter
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any, Tuple, Set

# Importa le funzioni necessarie da breeding_planner.py
try:
    import breeding_planner as bp
except ImportError:
    messagebox.showerror("Errore di Importazione", "Il file 'breeding_planner.py' non è stato trovato. Assicurati che sia nella stessa directory.")
    sys.exit(1)

# Importa le strutture dati e le funzioni logiche della Fase 3
try:
    from breeding_fase3 import PokemonBaseRichiestoF3, PianoAnalizzatoF3, analizza_e_calcola_costi_piano_ottimale
except ImportError:
    messagebox.showerror("Errore di Importazione", "Il file 'breeding_fase3.py' non è stato trovato. Assicurati che sia nella stessa directory.")
    sys.exit(1)


# --- Database Specie / Egg Group (Globale, caricato da file) ---
DB_SPECIE_EGG_GROUPS: Dict[str, Dict[str, Any]] = {}
POKEMON_NAMES_LIST: List[str] = []
NATURE_ITALIANO_LIST = [
    "Nessuna", "Ardita", "Schiva", "Audace", "Decisa", "Birbona", "Sicura", "Docile",
    "Placida", "Scaltra", "Fiacca", "Timida", "Lesta", "Seria", "Allegra",
    "Ingenua", "Modesta", "Mite", "Quieta", "Ritrosa", "Ardente", "Calma",
    "Gentile", "Vivace", "Cauta", "Furba"
]
IV_LIST = ["PS", "ATT", "DEF", "SP.ATT", "SP.DEF", "Velocità"]


def carica_pokemon_data_globale(filename="pokemon_data.json"):
    global DB_SPECIE_EGG_GROUPS, POKEMON_NAMES_LIST
    try:
        with open(filename, "r", encoding="utf-8") as f:
            data = json.load(f)
            if not isinstance(data, dict):
                messagebox.showerror("Errore Formato Dati", f"Il file '{filename}' non è un dizionario.")
                DB_SPECIE_EGG_GROUPS, POKEMON_NAMES_LIST = {}, []
                return False
            temp_db = {}
            for nome_pokemon, egg_groups_data in data.items():
                if not isinstance(nome_pokemon, str) or not isinstance(egg_groups_data, list):
                    print(f"Avviso: Voce non valida in '{filename}' saltata: {nome_pokemon}")
                    continue
                temp_db[nome_pokemon] = {"egg_groups": egg_groups_data, "specie_base": nome_pokemon}
            DB_SPECIE_EGG_GROUPS = temp_db
            POKEMON_NAMES_LIST = sorted(list(DB_SPECIE_EGG_GROUPS.keys()))
            print(f"Dati Pokémon globali caricati: {len(POKEMON_NAMES_LIST)} voci.")
            return True
    except FileNotFoundError:
        messagebox.showwarning("Attenzione", f"File dati Pokémon '{filename}' non trovato.")
    except json.JSONDecodeError:
        messagebox.showerror("Errore", f"Formato JSON errato in '{filename}'.")
    except Exception as e:
        messagebox.showerror("Errore Caricamento Dati", f"Errore imprevisto: {e}\n{traceback.format_exc()}")
    DB_SPECIE_EGG_GROUPS, POKEMON_NAMES_LIST = {}, []
    return False

def get_egg_groups(specie: Optional[str]) -> List[str]:
    if specie and specie in DB_SPECIE_EGG_GROUPS:
        return DB_SPECIE_EGG_GROUPS[specie].get("egg_groups", [])
    return []

def get_base_specie(specie: Optional[str]) -> Optional[str]:
    if specie and specie in DB_SPECIE_EGG_GROUPS:
        return DB_SPECIE_EGG_GROUPS[specie].get("specie_base", specie)
    return specie

class BreedingApp(tk.Tk):
    def __init__(self):
        global POKEMON_NAMES_LIST
        super().__init__()
        self.title("PokéMMO Breeding Planner GUI")
        self.geometry("1150x800")

        caricamento_ok = carica_pokemon_data_globale()
        if not caricamento_ok and not POKEMON_NAMES_LIST:
            POKEMON_NAMES_LIST = ["Pikachu", "Charizard", "Ditto", "Bulbasaur", "Eevee"]
            messagebox.showinfo("Info Dati Pokémon", "Utilizzo lista Pokémon di default. Per funzionalità complete, assicurati che 'pokemon_data.json' esista e sia nel formato corretto.")

        self.iv_vars = {stat: tk.BooleanVar() for stat in IV_LIST}
        self.natura_var = tk.StringVar()
        self.pokemon_target_nome_var = tk.StringVar()

        self.pokemon_posseduti_list: List[bp.PokemonPossedutoF2] = []

        self.piani_candidati_fase2_data: List[Dict[str, Any]] = []
        self.prezzi_base_raccolti: Dict[str, Dict[str, Optional[float]]] = {}
        self.entry_prezzi_widgets: Dict[str, Dict[str, tk.StringVar]] = {}
        self.file_output_per_fase3 = "fase2_output_per_fase3.json"

        style = ttk.Style(self)
        style.theme_use('clam')
        style.configure("TButton", padding=6, relief="flat", background="#E1E1E1")
        style.map("TButton", background=[('active', '#B0B0B0')])
        style.configure("TLabel", padding=5, anchor="w")
        style.configure("Treeview.Heading", font=('TkDefaultFont', 10, 'bold'))
        style.configure("Bold.TLabel", font=('TkDefaultFont', 10, 'bold'))

        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(expand=True, fill=tk.BOTH)

        self.notebook = ttk.Notebook(main_frame)
        self.tab_fase1_target = ttk.Frame(self.notebook, padding="10")
        self.tab_posseduti = ttk.Frame(self.notebook, padding="10")
        self.tab_prezzi_base = ttk.Frame(self.notebook, padding="10")
        self.tab_fase3_risultati = ttk.Frame(self.notebook, padding="10")

        self.notebook.add(self.tab_fase1_target, text=" Fase 1: Target & Genera Piani ")
        self.notebook.add(self.tab_posseduti, text=" Pokémon Posseduti ")
        self.notebook.add(self.tab_prezzi_base, text=" Prezzi Base Pokémon ")
        self.notebook.add(self.tab_fase3_risultati, text=" Fase 3: Piano Ottimale ")
        self.notebook.pack(expand=True, fill=tk.BOTH)

        self.crea_widgets_fase1_target()
        self.crea_widgets_posseduti()
        self.crea_widgets_inserimento_prezzi()
        self.crea_widgets_fase3_visualizzazione_risultati()

    def crea_widgets_fase1_target(self):
        frame = self.tab_fase1_target
        ttk.Label(frame, text="Definisci Pokémon Target:", style="Bold.TLabel").grid(row=0, column=0, columnspan=3, pady=(0,10), sticky="w")

        ttk.Label(frame, text="Nome Pokémon Target:").grid(row=1, column=0, sticky="w", padx=5, pady=3)
        self.entry_pokemon_nome = ttk.Combobox(frame, textvariable=self.pokemon_target_nome_var, values=POKEMON_NAMES_LIST, width=30)
        self.entry_pokemon_nome.grid(row=1, column=1, columnspan=2, sticky="ew", padx=5, pady=3)
        self.entry_pokemon_nome.bind('<KeyRelease>', self.aggiorna_suggerimenti_nome)

        ttk.Label(frame, text="IVs Desiderate:").grid(row=2, column=0, sticky="nw", padx=5, pady=7)
        iv_frame = ttk.Frame(frame)
        iv_frame.grid(row=2, column=1, columnspan=2, sticky="w", pady=5)
        for i, (stat, var) in enumerate(self.iv_vars.items()):
            cb = ttk.Checkbutton(iv_frame, text=stat, variable=var)
            cb.grid(row=i // 3, column=i % 3, padx=(0,15), pady=2, sticky="w")

        ttk.Label(frame, text="Natura Desiderata:").grid(row=3, column=0, sticky="w", padx=5, pady=3)
        self.combo_natura = ttk.Combobox(frame, textvariable=self.natura_var, values=NATURE_ITALIANO_LIST, state="readonly", width=30)
        self.combo_natura.grid(row=3, column=1, columnspan=2, sticky="ew", padx=5, pady=3)
        self.combo_natura.set("Nessuna")

        action_buttons_frame = ttk.Frame(frame)
        action_buttons_frame.grid(row=4, column=0, columnspan=3, pady=15, sticky="ew")
        action_buttons_frame.columnconfigure(0, weight=1)

        self.btn_genera_fase1 = ttk.Button(action_buttons_frame, text="1. Genera Piani (Fase 1)", command=self.esegui_fase1_wrapper)
        self.btn_genera_fase1.pack(pady=(10,2))

        self.btn_valuta_fase2 = ttk.Button(action_buttons_frame, text="2. Valuta Piani con Posseduti (Fase 2)", command=self.esegui_fase2_wrapper, state=tk.DISABLED)
        self.btn_valuta_fase2.pack(pady=2)

        btn_aggiungi_target_a_posseduti = ttk.Button(action_buttons_frame, text="Aggiungi Target Corrente ai Posseduti", command=self.aggiungi_target_a_posseduti_dialog)
        btn_aggiungi_target_a_posseduti.pack(pady=(10,2))

    def aggiorna_suggerimenti_nome(self, event=None, combobox_widget=None):
        widget = combobox_widget if combobox_widget else self.entry_pokemon_nome
        valore_corrente = widget.get()
        if valore_corrente:
            suggerimenti = [nome for nome in POKEMON_NAMES_LIST if valore_corrente.lower() in nome.lower()]
            widget['values'] = suggerimenti if suggerimenti else POKEMON_NAMES_LIST
        else:
            widget['values'] = POKEMON_NAMES_LIST

    def crea_widgets_posseduti(self):
        frame = self.tab_posseduti
        ttk.Label(frame, text="Gestione Pokémon Posseduti (in memoria):", style="Bold.TLabel").pack(pady=(0,10), anchor="w")
        cols = ("ID Utente", "Specie*", "Sesso", "Natura", "IVs", "Egg Groups")
        self.tree_posseduti = ttk.Treeview(frame, columns=cols, show="headings", height=15)
        for col in cols:
            self.tree_posseduti.heading(col, text=col)
            self.tree_posseduti.column(col, width=110, anchor="w", minwidth=50)
        self.tree_posseduti.pack(expand=True, fill=tk.BOTH, pady=5)
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill=tk.X, pady=5)
        ttk.Button(btn_frame, text="Aggiungi", command=self.aggiungi_pokemon_dialog_wrapper).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Modifica", command=self.modifica_pokemon_dialog).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Rimuovi", command=self.rimuovi_pokemon_selezionato).pack(side=tk.LEFT, padx=2)

        ttk.Label(btn_frame, text="I Pokémon sono gestiti solo in memoria.", font=('TkDefaultFont', 8, 'italic')).pack(side=tk.RIGHT, padx=5)


    def aggiorna_tree_posseduti(self):
        for i in self.tree_posseduti.get_children(): self.tree_posseduti.delete(i)
        for pkmn in self.pokemon_posseduti_list:
            iv_str = "/".join(pkmn.ivs) if pkmn.ivs else "N/A"
            egg_groups_str = ", ".join(pkmn.egg_groups) if pkmn.egg_groups else "N/A"
            self.tree_posseduti.insert("", "end", values=(
                pkmn.id_utente or "(Nessun ID)", pkmn.specie, pkmn.sesso or "N/A",
                pkmn.natura or "N/A", iv_str, egg_groups_str))

    def aggiungi_target_a_posseduti_dialog(self):
        nome_specie = self.pokemon_target_nome_var.get()
        if not nome_specie:
            messagebox.showerror("Errore", "La Specie del Pokémon Target è obbligatoria per aggiungerlo ai posseduti.")
            return
        ivs_sel = [s for s,v in self.iv_vars.items() if v.get()]
        natura = self.natura_var.get()
        if natura == "Nessuna": natura = ""
        pkmn_prefill = bp.PokemonPossedutoF2(id_utente="", specie=nome_specie, ivs=ivs_sel, natura=natura, sesso=None, egg_groups=get_egg_groups(nome_specie))
        self._internal_aggiungi_modifica_pokemon(pkmn_da_modificare=pkmn_prefill, index_da_modificare=None, dialog_title="Completa Dati Pokémon da Target")

    def aggiungi_pokemon_dialog_wrapper(self):
        self._internal_aggiungi_modifica_pokemon(pkmn_da_modificare=None, index_da_modificare=None, dialog_title="Aggiungi Pokémon Posseduto")

    def modifica_pokemon_dialog(self):
        selected_item_id = self.tree_posseduti.focus()
        if not selected_item_id: messagebox.showwarning("Attenzione", "Nessun Pokémon selezionato per la modifica."); return
        index = self.tree_posseduti.index(selected_item_id)
        pkmn_da_modificare = self.pokemon_posseduti_list[index]
        self._internal_aggiungi_modifica_pokemon(pkmn_da_modificare, index, "Modifica Pokémon Posseduto")

    def _internal_aggiungi_modifica_pokemon(self, pkmn_da_modificare: Optional[bp.PokemonPossedutoF2], index_da_modificare: Optional[int], dialog_title: str):
        dialog = PokemonInputDialog(self, title=dialog_title, pokemon_data=pkmn_da_modificare)
        if dialog.result:
            data = dialog.result
            if not data["specie"]:
                messagebox.showerror("Errore", "La Specie è obbligatoria.")
                return
            id_fornito = data["id_utente"]
            if id_fornito:
                for idx, p in enumerate(self.pokemon_posseduti_list):
                    if index_da_modificare is not None and idx == index_da_modificare: continue
                    if p.id_utente and p.id_utente == id_fornito:
                        messagebox.showerror("Errore", f"L'ID Utente '{id_fornito}' è già utilizzato da un altro Pokémon.")
                        return

            pkmn_obj = bp.PokemonPossedutoF2(
                id_utente=id_fornito,
                ivs=sorted(list(set(data["ivs"]))),
                natura=data["natura"] if data["natura"] != "Nessuna" else "",
                specie=data["specie"],
                sesso=data["sesso"] if data["sesso"] != "Nessuno" else None,
                egg_groups=get_egg_groups(data["specie"]))

            if index_da_modificare is not None: self.pokemon_posseduti_list[index_da_modificare] = pkmn_obj
            else: self.pokemon_posseduti_list.append(pkmn_obj)
            self.aggiorna_tree_posseduti()

    def rimuovi_pokemon_selezionato(self):
        selected_item_id = self.tree_posseduti.focus()
        if not selected_item_id: messagebox.showwarning("Attenzione", "Nessun Pokémon selezionato."); return
        if messagebox.askyesno("Conferma", "Rimuovere il Pokémon selezionato?"):
            index = self.tree_posseduti.index(selected_item_id)
            del self.pokemon_posseduti_list[index]
            self.aggiorna_tree_posseduti()

    def crea_widgets_inserimento_prezzi(self):
        frame = self.tab_prezzi_base
        ttk.Label(frame, text="Inserisci Prezzi Base per IV e Nature Singole:", style="Bold.TLabel").pack(pady=(0,5), anchor="w")
        self.piani_candidati_prezzi_outer_frame = ttk.Frame(frame)
        self.piani_candidati_prezzi_outer_frame.pack(expand=True, fill=tk.BOTH, pady=5)

    def crea_widgets_fase3_visualizzazione_risultati(self):
        frame = self.tab_fase3_risultati
        ttk.Label(frame, text="Fase 3: Piano di Breeding Ottimale Calcolato", style="Bold.TLabel").pack(pady=(0,10), anchor="w")
        self.btn_esegui_fase3 = ttk.Button(frame, text="3. Calcola Piano Migliore con Costi (Fase 3)", command=self.esegui_fase3_con_logica_separata, state=tk.DISABLED)
        self.btn_esegui_fase3.pack(pady=10)
        self.output_fase3_text = tk.Text(frame, wrap=tk.WORD, height=25, width=100, relief=tk.SUNKEN, borderwidth=1)
        self.output_fase3_text.pack(expand=True, fill=tk.BOTH, pady=5)
        self.output_fase3_text.config(state=tk.DISABLED)

    def esegui_fase1_wrapper(self):
        ivs_sel = [s for s,v in self.iv_vars.items() if v.get()]
        natura_gui = self.natura_var.get()
        con_natura = natura_gui != "Nessuna"
        natura_spec = natura_gui if con_natura else ""
        num_iv = len(ivs_sel)
        if num_iv == 0 and not con_natura: messagebox.showerror("Errore Input", "Seleziona almeno un IV o una Natura per la Fase 1."); return

        modalita_op = f"{num_iv}IV"
        try:
            print(f"Esecuzione Fase 1: Modalità={modalita_op}, Natura={natura_spec or 'N/A'}, IVs={ivs_sel}")
            bp.run_fase1(modalita_op_base=modalita_op, con_natura_obiettivo=con_natura, natura_obiettivo_spec=natura_spec, stats_target_config=ivs_sel)
            messagebox.showinfo("Fase 1 Completata", "Piani generati in 'piani_dati.json'.\nOra puoi valutare i piani con i tuoi Pokémon posseduti.")
            self.btn_valuta_fase2.config(state=tk.NORMAL)
            self.notebook.select(self.tab_fase1_target)
        except Exception as e: messagebox.showerror("Errore Fase 1", f"Si è verificato un errore: {e}\n{traceback.format_exc()}")

    def esegui_fase2_wrapper(self):
        f_piani = "piani_dati.json"
        f_debug = "fase2_debug_log.txt"

        if not os.path.exists(f_piani):
            messagebox.showerror("Errore", f"File dei piani '{f_piani}' non trovato. Esegui prima la Fase 1.")
            return

        if not self.pokemon_posseduti_list:
             messagebox.showwarning("Attenzione Fase 2", "Nessun Pokémon posseduto in memoria. La valutazione potrebbe non essere significativa.")
        else:
            messagebox.showinfo("Info Fase 2", f"Utilizzo di {len(self.pokemon_posseduti_list)} Pokémon posseduti dalla memoria per la valutazione.")

        try:
            print("Esecuzione Fase 2 (da breeding_planner.py)...")
            # Passa la lista dei Pokémon posseduti direttamente
            bp.run_fase2(f_piani, self.pokemon_posseduti_list, f_debug, self.file_output_per_fase3)

            messagebox.showinfo("Fase 2 Completata", f"Valutazione completata. I piani candidati sono stati salvati in '{self.file_output_per_fase3}'.\nOra puoi inserire i prezzi nella scheda 'Prezzi Base Pokémon'.")
            self._carica_e_mostra_interfaccia_prezzi()
            self.notebook.select(self.tab_prezzi_base)
            self.btn_esegui_fase3.config(state=tk.NORMAL)
        except Exception as e:
            messagebox.showerror("Errore Fase 2", f"Si è verificato un errore: {e}\n{traceback.format_exc()}")
            self.btn_esegui_fase3.config(state=tk.DISABLED)

    def _carica_e_mostra_interfaccia_prezzi(self):
        for widget in self.piani_candidati_prezzi_outer_frame.winfo_children(): widget.destroy()
        self.piani_candidati_fase2_data = self._carica_dati_piani_da_json_fase2_output(self.file_output_per_fase3)
        self.prezzi_base_raccolti.clear(); self.entry_prezzi_widgets.clear()

        if not self.piani_candidati_fase2_data:
            ttk.Label(self.piani_candidati_prezzi_outer_frame, text="Nessun piano candidato trovato dalla Fase 2.").pack(pady=20)
            self.btn_esegui_fase3.config(state=tk.DISABLED); return

        iv_pure, nature_pure = set(), set()
        for piano_data in self.piani_candidati_fase2_data:
            for desc_base in piano_data.get("pokemon_base_necessari_calcolati", {}).keys():
                tipo, stat_nat, _ = self._parse_desc_base_gui(desc_base)
                if tipo == "IV": iv_pure.add(stat_nat)
                elif tipo == "Natura": nature_pure.add(stat_nat)

        specie_tg_globale = self.pokemon_target_nome_var.get() or "Target (Non Def.)"
        specie_base_tg_globale = get_base_specie(specie_tg_globale) or specie_tg_globale


        if not iv_pure and not nature_pure:
            ttk.Label(self.piani_candidati_prezzi_outer_frame, text="Nessun Pokémon base (IV/Natura singola) da prezzare.").pack(pady=10)
            return

        ttk.Label(self.piani_candidati_prezzi_outer_frame, text=f"Specie Target per prezzi '(... Target)': {specie_base_tg_globale}", style="Bold.TLabel").pack(pady=(0,10), anchor="w")

        canvas = tk.Canvas(self.piani_candidati_prezzi_outer_frame); scrollbar = ttk.Scrollbar(self.piani_candidati_prezzi_outer_frame, orient="vertical", command=canvas.yview)
        s_frame = ttk.Frame(canvas); s_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=s_frame, anchor="nw"); canvas.configure(yscrollcommand=scrollbar.set)

        price_conf = [
            ("femmina_specie_target", f"Femmina ({specie_base_tg_globale})"),
            ("maschio_specie_target", f"Maschio ({specie_base_tg_globale})"),
            ("femmina_egg_group", "Femmina (Egg Group)"),
            ("maschio_egg_group", "Maschio (Egg Group)"),
            ("ditto", "Ditto")]

        if iv_pure:
            ttk.Label(s_frame, text="Prezzi per Pokémon con Singola IV:", style="Bold.TLabel").pack(pady=(5,2), anchor="w")
            for stat in sorted(list(iv_pure)):
                id_key = f"IV_{stat}"; self.entry_prezzi_widgets[id_key] = {}
                lf = ttk.LabelFrame(s_frame, text=f"IV: {stat}", padding=5)
                lf.pack(pady=(2,8), padx=3, fill=tk.X, expand=True)
                for i, (k, lbl) in enumerate(price_conf):
                    ttk.Label(lf, text=f"{lbl}:").grid(row=i, column=0, sticky="w", padx=(5,2), pady=1)
                    var = tk.StringVar(); ttk.Entry(lf, textvariable=var, width=10).grid(row=i, column=1, padx=(0,5), pady=1, sticky="ew")
                    self.entry_prezzi_widgets[id_key][k] = var; lf.grid_columnconfigure(1, weight=1)
        if nature_pure:
            ttk.Label(s_frame, text="Prezzi per Pokémon con Singola Natura:", style="Bold.TLabel").pack(pady=(10,2), anchor="w")
            for nat in sorted(list(nature_pure)):
                id_key = f"Natura_{nat}"; self.entry_prezzi_widgets[id_key] = {}
                lf = ttk.LabelFrame(s_frame, text=f"Natura: {nat}", padding=5)
                lf.pack(pady=(2,8), padx=3, fill=tk.X, expand=True)
                for i, (k, lbl) in enumerate(price_conf):
                    ttk.Label(lf, text=f"{lbl}:").grid(row=i, column=0, sticky="w", padx=(5,2), pady=1)
                    var = tk.StringVar(); ttk.Entry(lf, textvariable=var, width=10).grid(row=i, column=1, padx=(0,5), pady=1, sticky="ew")
                    self.entry_prezzi_widgets[id_key][k] = var; lf.grid_columnconfigure(1, weight=1)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True); scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def _parse_desc_base_gui(self, desc_base: str) -> Tuple[Optional[str], str, Optional[str]]:
        tipo, stat_o_natura, colore = None, desc_base, None
        try:
            if "Solo Natura:" in desc_base: tipo, stat_o_natura = "Natura", desc_base.split(": ")[1].strip()
            elif "Solo IV:" in desc_base:
                tipo = "IV"; parts = desc_base.split(": ")[1].split("(")
                stat_o_natura = parts[0].strip()
                if len(parts) > 1: colore = parts[1].replace(")", "").strip()
            elif "Da Procurare" in desc_base:
                tipo = "Da Procurare"
                if "(Definizione:" in desc_base: stat_o_natura = desc_base.split("(Definizione:")[1].split(")")[0].strip()
                elif "(nome:" in desc_base: stat_o_natura = desc_base.split("(nome:")[1].split(")")[0].strip()
        except IndexError: print(f"Avviso parsing GUI: {desc_base}")
        return tipo, stat_o_natura, colore

    def _carica_dati_piani_da_json_fase2_output(self, filename: str) -> List[Dict[str, Any]]:
        try:
            with open(filename, "r", encoding="utf-8") as f: data = json.load(f)
            if isinstance(data, list): return data
            messagebox.showerror("Errore Dati", f"File '{filename}' non contiene una lista."); return []
        except FileNotFoundError: messagebox.showerror("Errore", f"File '{filename}' non trovato."); return []
        except json.JSONDecodeError: messagebox.showerror("Errore", f"JSON non valido in '{filename}'."); return []
        except Exception as e: messagebox.showerror("Errore Caricamento Piani", f"Errore: {e}\n{traceback.format_exc()}"); return []

    def esegui_fase3_con_logica_separata(self):
        self.output_fase3_text.config(state=tk.NORMAL); self.output_fase3_text.delete("1.0", tk.END)

        self.prezzi_base_raccolti.clear()
        for id_prezzo_widget, vars_per_tipo_prezzo_dict in self.entry_prezzi_widgets.items():
            self.prezzi_base_raccolti[id_prezzo_widget] = {}
            for tipo_prezzo_key, var_str_obj in vars_per_tipo_prezzo_dict.items():
                val_str = var_str_obj.get()
                try: self.prezzi_base_raccolti[id_prezzo_widget][tipo_prezzo_key] = float(val_str) if val_str else None
                except ValueError: self.prezzi_base_raccolti[id_prezzo_widget][tipo_prezzo_key] = None

        specie_globale_target_gui = self.pokemon_target_nome_var.get()
        if not self.piani_candidati_fase2_data:
            messagebox.showerror("Errore Fase 3", "Nessun dato piani Fase 2. Esegui prima la Fase 2.")
            self.output_fase3_text.insert(tk.END, "Nessun dato dei piani candidati dalla Fase 2 disponibile.");
            self.output_fase3_text.config(state=tk.DISABLED); return

        try:
            piano_finale_scelto = analizza_e_calcola_costi_piano_ottimale(
                piani_candidati_data=self.piani_candidati_fase2_data,
                prezzi_base_raccolti_gui=self.prezzi_base_raccolti,
                specie_target_globale_gui=specie_globale_target_gui,
                pokemon_names_list_globale=POKEMON_NAMES_LIST,
                fn_get_base_specie=get_base_specie
            )
        except Exception as e:
            messagebox.showerror("Errore Calcolo Fase 3", f"Errore: {e}\n{traceback.format_exc()}")
            self.output_fase3_text.insert(tk.END, f"Errore durante il calcolo della Fase 3: {e}");
            self.output_fase3_text.config(state=tk.DISABLED); return

        out_text_widget = self.output_fase3_text
        if piano_finale_scelto:
            out_text_widget.insert(tk.END, f"--- Piano Breeding OTTIMALE (ID Fase 1: {piano_finale_scelto.id_piano_fase1}) ---\n")
            specie_target_eff_piano = piano_finale_scelto.specie_target_piano or get_base_specie(specie_globale_target_gui) or 'Non specificata'
            out_text_widget.insert(tk.END, f"Specie Target Effettiva del Piano (per prezzi): {specie_target_eff_piano}\n")
            leg_str = ", ".join([f'{k}="{v}"' for k,v in piano_finale_scelto.legenda_usata.items()])
            out_text_widget.insert(tk.END, f"Legenda Usata: {leg_str if leg_str else 'Nessuna'}\n")
            out_text_widget.insert(tk.END, f"Punteggio Fase 2: {piano_finale_scelto.punteggio_fase2:.2f}\n")
            out_text_widget.insert(tk.END, f"Pokémon Richiesti Soddisfatti da Posseduti (Fase 2): {piano_finale_scelto.match_fase2}\n")
            poss_usati_str = ", ".join(sorted([pid if pid else "(Nessun ID)" for pid in piano_finale_scelto.posseduti_usati_fase2]))
            out_text_widget.insert(tk.END, f"Pokémon Posseduti Unici Utilizzati nel Piano: {len(piano_finale_scelto.posseduti_usati_fase2)} ({poss_usati_str if poss_usati_str else 'Nessuno'})\n")
            out_text_widget.insert(tk.END, f"COSTO TOTALE STIMATO POKÉMON BASE (da acquistare): {piano_finale_scelto.costo_totale_stimato_base:.2f}\n\n")
            out_text_widget.insert(tk.END, "Dettaglio Pokémon Base da Acquistare (non coperti da posseduti):\n")

            if piano_finale_scelto.dettaglio_base_richiesti_con_costi:
                for base in piano_finale_scelto.dettaglio_base_richiesti_con_costi:
                    if base.quantita_necessaria > 0:
                        out_text_widget.insert(tk.END, f"  - {base.descrizione} x{base.quantita_necessaria}\n")
                        if base.tipo != "Da Procurare":
                            st_nome = specie_target_eff_piano
                            opts = []
                            if base.costo_femmina_target is not None:
                                opts.append(f"F {st_nome}: {base.costo_femmina_target}")
                            else: opts.append(f"F {st_nome}: N/P")

                            prezzi_per_id_base = self.prezzi_base_raccolti.get(base.id_univoco_base, {})
                            costo_m_target_val = prezzi_per_id_base.get("maschio_specie_target")
                            if costo_m_target_val is not None: opts.append(f"M {st_nome}: {costo_m_target_val}")
                            else: opts.append(f"M {st_nome}: N/P")

                            costo_f_egg_val = prezzi_per_id_base.get("femmina_egg_group")
                            if costo_f_egg_val is not None: opts.append(f"F EggG: {costo_f_egg_val}")
                            else: opts.append(f"F EggG: N/P")


                            if base.costo_maschio_egg_group is not None:
                                opts.append(f"M EggG: {base.costo_maschio_egg_group}")
                            else: opts.append(f"M EggG: N/P")

                            if base.costo_ditto is not None:
                                opts.append(f"Ditto: {base.costo_ditto}")
                            else: opts.append(f"Ditto: N/P")

                            out_text_widget.insert(tk.END, f"    Opzioni Prezzo (ID Base: {base.id_univoco_base}): {'; '.join(opts)}\n")
                            out_text_widget.insert(tk.END, f"    -> Scelta Più Economica: {base.scelta_migliore or 'N/A'} @ {base.costo_scelta_migliore if base.costo_scelta_migliore is not None else 'Non Prezzato'}\n")
                        else: out_text_widget.insert(tk.END, f"    -> {base.scelta_migliore}\n")
            else: out_text_widget.insert(tk.END, "  Nessun Pokémon base aggiuntivo da acquistare (o nessun prezzo utile inserito).\n")

            if piano_finale_scelto.note_compatibilita:
                out_text_widget.insert(tk.END, "\nNote Addizionali sul Calcolo Costi:\n")
                for nota in piano_finale_scelto.note_compatibilita: out_text_widget.insert(tk.END, f"  - {nota}\n")
        else: out_text_widget.insert(tk.END, "Nessun piano ottimale trovato o nessun piano candidato valido dopo l'analisi dei costi.")
        out_text_widget.config(state=tk.DISABLED); self.notebook.select(self.tab_fase3_risultati)


class PokemonInputDialog(simpledialog.Dialog):
    def __init__(self, parent, title=None, pokemon_data: Optional[bp.PokemonPossedutoF2]=None):
        self.app_parent = parent; self.pokemon_data = pokemon_data
        self.iv_vars_dialog = {stat: tk.BooleanVar() for stat in IV_LIST}
        self.natura_var_dialog, self.sesso_var_dialog = tk.StringVar(), tk.StringVar()
        self.specie_var_dialog = tk.StringVar()
        self.id_utente_var_dialog = tk.StringVar()

        if pokemon_data:
            self.id_utente_var_dialog.set(pokemon_data.id_utente or "")
            for iv in pokemon_data.ivs:
                if iv in self.iv_vars_dialog: self.iv_vars_dialog[iv].set(True)
            self.natura_var_dialog.set(pokemon_data.natura or "Nessuna")
            self.specie_var_dialog.set(pokemon_data.specie or "")
            self.sesso_var_dialog.set(pokemon_data.sesso or "Nessuno")
        else:
            self.id_utente_var_dialog.set("")
            self.natura_var_dialog.set("Nessuna")
            self.sesso_var_dialog.set("Nessuno")
            self.specie_var_dialog.set("")
        super().__init__(parent, title)

    def body(self, master_frame):
        ttk.Label(master_frame, text="ID Utente:").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        self.entry_id = ttk.Entry(master_frame, textvariable=self.id_utente_var_dialog, width=30)
        self.entry_id.grid(row=0, column=1, columnspan=3, sticky="ew", padx=5, pady=2)

        ttk.Label(master_frame, text="Specie*:").grid(row=1, column=0, sticky="w", padx=5, pady=2)
        self.entry_specie_dialog = ttk.Combobox(master_frame, textvariable=self.specie_var_dialog, values=POKEMON_NAMES_LIST, width=28)
        self.entry_specie_dialog.grid(row=1, column=1, columnspan=3, sticky="ew", padx=5, pady=2)
        self.entry_specie_dialog.bind('<KeyRelease>', lambda e: self.app_parent.aggiorna_suggerimenti_nome(combobox_widget=self.entry_specie_dialog))

        ttk.Label(master_frame, text="IVs:").grid(row=2, column=0, sticky="nw", padx=5, pady=5)
        iv_frame = ttk.Frame(master_frame); iv_frame.grid(row=2, column=1, columnspan=3, sticky="w")
        for i, (stat, var) in enumerate(self.iv_vars_dialog.items()):
            cb = ttk.Checkbutton(iv_frame, text=stat, variable=var); cb.grid(row=i//3, column=i%3, padx=2, sticky="w")

        ttk.Label(master_frame, text="Natura:").grid(row=3, column=0, sticky="w", padx=5, pady=2)
        self.combo_natura_dialog = ttk.Combobox(master_frame, textvariable=self.natura_var_dialog, values=NATURE_ITALIANO_LIST, state="readonly", width=28)
        self.combo_natura_dialog.grid(row=3, column=1, columnspan=3, sticky="ew", padx=5, pady=2)

        ttk.Label(master_frame, text="Sesso:").grid(row=4, column=0, sticky="w", padx=5, pady=2)
        self.combo_sesso_dialog = ttk.Combobox(master_frame, textvariable=self.sesso_var_dialog, values=["Nessuno", "M", "F"], state="readonly", width=28)
        self.combo_sesso_dialog.grid(row=4, column=1, columnspan=3, sticky="ew", padx=5, pady=2)

        ttk.Label(master_frame, text="* La Specie è obbligatoria", font=('TkDefaultFont', 8, 'italic')).grid(row=5, column=1, columnspan=3, sticky="w", padx=5, pady=(5,0))
        return self.entry_specie_dialog

    def apply(self):
        self.result = {"id_utente": self.id_utente_var_dialog.get(), "ivs": [s for s,v in self.iv_vars_dialog.items() if v.get()],
                       "natura": self.natura_var_dialog.get(), "specie": self.specie_var_dialog.get(), "sesso": self.sesso_var_dialog.get()}

if __name__ == '__main__':
    import traceback
    try:
        app = BreedingApp()
        app.mainloop()
    except Exception as e:
        print(f"Errore fatale nell'applicazione: {e}")
        print(traceback.format_exc())
        messagebox.showerror("Errore Fatale", f"Si è verificato un errore critico:\n{e}\n\nL'applicazione verrà chiusa. Controlla la console per i dettagli.")

[end of breeding_gui.py]
