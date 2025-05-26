# gui_breeder.py
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
from typing import Set, Optional, List
import pokemon_breeder as core  # Questo ora userà il pokemon_breeder.py aggiornato


class BreedingPlannerGUI_v8:  # Mantengo il nome per coerenza, ma il backend è aggiornato
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("PokéMMO Breeding Planner v12 (A* Cost Update)")
        self.root.geometry("950x800")

        if not core.POKEMON_EGG_GROUPS_RAW:
            messagebox.showwarning(
                "Dati Mancanti",
                "Il file 'pokemon_data.json' non è stato trovato o è illeggibile.\n"
                "L'autocompletamento e la validazione delle specie non funzioneranno."
            )

        self.user_inventory: List[core.Pokemon] = []

        self.autocomplete_window: Optional[tk.Toplevel] = None
        self.autocomplete_listbox: Optional[tk.Listbox] = None
        self.active_entry_var: Optional[tk.StringVar] = None
        self.active_entry_widget: Optional[ttk.Entry] = None

        style = ttk.Style()
        style.theme_use('clam')
        style.configure("TNotebook.Tab", padding=[10, 5], font=('TkDefaultFont', 10, 'bold'))
        style.configure("TButton", padding=6, relief="flat", background="#ccc")
        style.map("TButton", background=[('active', '#bbb')])

        notebook = ttk.Notebook(root)
        notebook.pack(expand=True, fill='both', padx=10, pady=10)

        planner_tab = ttk.Frame(notebook, padding="10")
        inventory_tab = ttk.Frame(notebook, padding="10")

        notebook.add(planner_tab, text='Pianificatore Breeding')
        notebook.add(inventory_tab, text='Inventario Pokémon')

        self._create_planner_tab(planner_tab)
        self._create_inventory_tab(inventory_tab)

        self.root.bind_all("<Button-1>", self._handle_global_click, add="+")

    def _handle_global_click(self, event: tk.Event):
        if self.autocomplete_window and self.autocomplete_window.winfo_exists():
            clicked_widget = event.widget
            if self.active_entry_widget and clicked_widget == self.active_entry_widget: return
            current_widget = clicked_widget
            while current_widget:
                if current_widget == self.autocomplete_window: return
                try:
                    current_widget = current_widget.master
                except AttributeError:
                    current_widget = None
            self._hide_autocomplete()

    def _prevent_text_edit(self, event: tk.Event) -> Optional[str]:
        if event.state & 0x4:
            if event.keysym.lower() in ('c', 'a'):
                return None
            elif event.keysym.lower() in ('v', 'x', 'd', 'h'):
                return "break"
            else:
                return None
        if event.state & 0x1:
            if event.keysym in ("Left", "Right", "Up", "Down", "Home", "End", "Prior", "Next"):
                return None
            elif event.keysym.lower() in ('insert', 'delete'):
                return "break"
        if event.keysym in ("Left", "Right", "Up", "Down", "Home", "End", "Prior", "Next", "Tab", "ISO_Left_Tab",
                            "Escape"): return None
        if event.keysym in ("BackSpace", "Delete", "Return", "KP_Enter") or \
                (len(event.char) > 0 and event.char.isprintable()):
            return "break"
        return None

    def _make_text_readonly_selectable(self, text_widget: scrolledtext.ScrolledText):
        text_widget.config(state=tk.NORMAL)
        text_widget.bind("<KeyPress>", self._prevent_text_edit)
        text_widget.bind("<FocusIn>", self._on_text_area_focus_in)

    def _on_text_area_focus_in(self, event=None):
        self._hide_autocomplete()

    def _show_autocomplete(self, entry_var: tk.StringVar, entry_widget: ttk.Entry, data: List[str]):
        if self.autocomplete_window and self.autocomplete_window.winfo_exists():
            if self.autocomplete_listbox:
                self.autocomplete_listbox.delete(0, tk.END)
                for item in data: self.autocomplete_listbox.insert(tk.END, item)
                if not data: self._hide_autocomplete(); return
                self.autocomplete_listbox.config(height=min(5, len(data)))
                if self.autocomplete_listbox.size() > 0:
                    self.autocomplete_listbox.selection_set(0)
                    self.autocomplete_listbox.activate(0)
            x = entry_widget.winfo_rootx();
            y = entry_widget.winfo_rooty() + entry_widget.winfo_height()
            self.autocomplete_window.wm_geometry(f"+{x}+{y}")
            self.autocomplete_window.lift()
            entry_widget.focus_set()
            return
        self._hide_autocomplete()
        self.active_entry_var = entry_var;
        self.active_entry_widget = entry_widget
        self.autocomplete_window = tk.Toplevel(self.root)
        self.autocomplete_window.wm_overrideredirect(True);
        self.autocomplete_window.wm_transient(self.root)
        self.autocomplete_listbox = tk.Listbox(self.autocomplete_window, height=min(5, len(data)),
                                               exportselection=False, relief="solid", borderwidth=1)
        for item in data: self.autocomplete_listbox.insert(tk.END, item)
        if not data: self._hide_autocomplete(); return
        self.autocomplete_listbox.pack(fill=tk.BOTH, expand=True)
        self.autocomplete_listbox.bind("<<ListboxSelect>>", self._on_autocomplete_select_click)
        self.autocomplete_listbox.bind("<Return>", self._on_autocomplete_select_enter)
        self.autocomplete_listbox.bind("<KP_Enter>", self._on_autocomplete_select_enter)
        self.autocomplete_listbox.bind("<Escape>", lambda e: self._hide_autocomplete(refocus_entry=True))
        x = entry_widget.winfo_rootx();
        y = entry_widget.winfo_rooty() + entry_widget.winfo_height()
        self.autocomplete_window.wm_geometry(f"+{x}+{y}")
        self.autocomplete_window.deiconify()
        if self.autocomplete_listbox.size() > 0:
            self.autocomplete_listbox.selection_set(0);
            self.autocomplete_listbox.activate(0)
        entry_widget.focus_set()

    def _hide_autocomplete(self, refocus_entry=False):
        current_active_entry = self.active_entry_widget
        if self.autocomplete_window and self.autocomplete_window.winfo_exists(): self.autocomplete_window.destroy()
        self.autocomplete_window = None;
        self.autocomplete_listbox = None;
        self.active_entry_var = None
        if refocus_entry and current_active_entry and current_active_entry.winfo_exists(): current_active_entry.focus_set()
        if not refocus_entry: self.active_entry_widget = None

    def _on_autocomplete_select_click(self, event=None):
        self._perform_autocomplete_selection()

    def _on_autocomplete_select_enter(self, event=None):
        self._perform_autocomplete_selection(); return "break"

    def _perform_autocomplete_selection(self):
        entry_to_refocus = self.active_entry_widget
        if self.autocomplete_listbox and self.active_entry_var:
            selection_indices = self.autocomplete_listbox.curselection()
            if selection_indices: self.active_entry_var.set(self.autocomplete_listbox.get(selection_indices[0]))
        self._hide_autocomplete(refocus_entry=False)
        if entry_to_refocus and entry_to_refocus.winfo_exists():
            entry_to_refocus.focus_set();
            entry_to_refocus.icursor(tk.END)
        self.active_entry_widget = None

    def _on_species_entry_keyup(self, event: tk.Event, entry_var: tk.StringVar, entry_widget: ttk.Entry):
        if event.keysym in ("Shift_L", "Shift_R", "Control_L", "Control_R", "Alt_L", "Alt_R", "Caps_Lock", "Num_Lock",
                            "Scroll_Lock", "Tab", "ISO_Left_Tab", "FocusOut", "FocusIn"): return
        if event.keysym == "Escape": self._hide_autocomplete(refocus_entry=True); return
        if event.keysym in ("Return", "KP_Enter"):
            if self.autocomplete_listbox and self.autocomplete_listbox.winfo_ismapped(): self._perform_autocomplete_selection()
            return
        if event.keysym in ("Up", "Down"):
            if self.autocomplete_listbox and self.autocomplete_listbox.winfo_ismapped():
                self.autocomplete_listbox.focus_set()
                if not self.autocomplete_listbox.curselection() and self.autocomplete_listbox.size() > 0:
                    idx_to_select = 0 if event.keysym == "Down" else tk.END
                    self.autocomplete_listbox.selection_set(idx_to_select)
                    self.autocomplete_listbox.activate(
                        self.autocomplete_listbox.curselection()[0] if self.autocomplete_listbox.curselection() else 0)
            return
        current_value = entry_var.get()
        if not current_value: self._hide_autocomplete(refocus_entry=False); return
        suggestions = [name for name in core.ALL_POKEMON_NAMES if name.lower().startswith(current_value.lower())]
        if suggestions:
            self._show_autocomplete(entry_var, entry_widget, suggestions)
        else:
            self._hide_autocomplete(refocus_entry=False)

    def _handle_entry_down_arrow(self, entry_widget: ttk.Entry):
        if self.autocomplete_listbox and self.autocomplete_listbox.winfo_ismapped() and self.autocomplete_listbox.size() > 0:
            self.autocomplete_listbox.focus_set()
            if not self.autocomplete_listbox.curselection():
                self.autocomplete_listbox.selection_set(0);
                self.autocomplete_listbox.activate(0)
        return "break"

    def _create_planner_tab(self, tab: ttk.Frame):
        target_frame = ttk.LabelFrame(tab, text="1. Definisci il Pokémon Target", padding=10)
        target_frame.pack(fill=tk.X, pady=5, padx=5)
        ttk.Label(target_frame, text="Specie:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.target_species_var = tk.StringVar()
        self.target_species_entry = ttk.Entry(target_frame, textvariable=self.target_species_var, width=30)
        self.target_species_entry.grid(row=0, column=1, sticky="ew", padx=5)
        self.target_species_entry.bind("<KeyRelease>",
                                       lambda e: self._on_species_entry_keyup(e, self.target_species_var,
                                                                              self.target_species_entry))
        self.target_species_entry.bind("<Down>", lambda e: self._handle_entry_down_arrow(self.target_species_entry))
        natures = ["NEUTRAL"] + core.ALL_NATURES
        ttk.Label(target_frame, text="Natura:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.target_nature_var = tk.StringVar(value="NEUTRAL")
        ttk.Combobox(target_frame, textvariable=self.target_nature_var, values=natures, state="readonly",
                     width=28).grid(row=1, column=1, sticky="ew", padx=5)
        genders = ["Maschio", "Femmina", "Genderless"]
        ttk.Label(target_frame, text="Sesso:").grid(row=2, column=0, sticky="w", padx=5, pady=5)
        self.target_gender_var = tk.StringVar(value="Maschio")
        ttk.Combobox(target_frame, textvariable=self.target_gender_var, values=genders, state="readonly",
                     width=28).grid(row=2, column=1, sticky="ew", padx=5)
        iv_frame = ttk.LabelFrame(target_frame, text="IVs a 31 desiderati")
        iv_frame.grid(row=0, column=2, rowspan=3, padx=10, pady=5, sticky="ns")
        self.target_iv_vars = {stat: tk.BooleanVar() for stat in core.IV_STATS}
        for i, stat in enumerate(core.IV_STATS): ttk.Checkbutton(iv_frame, text=stat,
                                                                 variable=self.target_iv_vars[stat]).pack(anchor="w",
                                                                                                          padx=5,
                                                                                                          pady=2)
        target_frame.columnconfigure(1, weight=1)
        run_button = ttk.Button(tab, text="Genera Piano di Breeding Ottimale", command=self._run_planning)
        run_button.pack(pady=20)
        result_frame = ttk.LabelFrame(tab, text="Piano di Breeding Suggerito", padding=10)
        result_frame.pack(fill=tk.BOTH, expand=True, pady=5, padx=5)
        self.result_text = scrolledtext.ScrolledText(result_frame, wrap=tk.WORD, font=("Courier New", 10), height=15)
        self.result_text.pack(fill=tk.BOTH, expand=True)
        self._make_text_readonly_selectable(self.result_text)

    def _run_planning(self):
        self._hide_autocomplete(refocus_entry=False)
        species_input = self.target_species_var.get()
        if not species_input: messagebox.showerror("Errore Input", "La specie del Pokémon target è richiesta."); return
        species = species_input.capitalize()
        if species.lower() not in core.POKEMON_EGG_GROUPS_RAW and species.lower() != "ditto":
            messagebox.showerror("Errore Input", f"Specie '{species}' non valida o non trovata nei dati.");
            return
        nature = self.target_nature_var.get()
        gender = self.target_gender_var.get()
        ivs_to_get: Set[str] = {stat for stat, var in self.target_iv_vars.items() if var.get()}

        self.result_text.config(state=tk.NORMAL)
        self.result_text.delete('1.0', tk.END)
        if not ivs_to_get and nature == "NEUTRAL":
            messagebox.showinfo("Info", "Nessun IV o natura specifica richiesta.")
            self.result_text.insert(tk.END, "Nessun piano necessario: nessun IV o natura specifica richiesta.")
            self._make_text_readonly_selectable(self.result_text);
            return

        self.result_text.insert(tk.END,
                                "Ricerca del piano di breeding ottimale in corso...\n(Potrebbe richiedere del tempo)\n\n")
        self.root.update_idletasks()

        try:
            plan_result = core.find_optimal_breeding_plan(
                target_species=species,
                target_ivs=ivs_to_get,
                target_nature=nature,
                target_gender=gender,
                owned_pokemon_list=self.user_inventory
            )
            self.result_text.delete('1.0', tk.END)
            if plan_result:
                plan_steps_for_display: List[core.BreedingStepDetailed] = []
                total_cost_str = "N/D (calcolo costo da implementare)"

                if isinstance(plan_result, core.BreedingNode):
                    total_cost_str = str(plan_result.g_cost)
                    owned_map = {p.id: p for p in self.user_inventory}
                    plan_steps_for_display = core.reconstruct_plan(plan_result, gender, owned_map)
                elif isinstance(plan_result, list) and (
                        not plan_result or all(isinstance(step, core.BreedingStepDetailed) for step in plan_result)):
                    plan_steps_for_display = plan_result
                else:
                    plan_steps_for_display.append(
                        core.BreedingStepDetailed(
                            core.Pokemon("Errore", set(), "NEUTRAL", "N/A", source_info="Formato Piano Sconosciuto"),
                            core.Pokemon("N/A", set(), "NEUTRAL", "N/A"), None,
                            core.Pokemon("N/A", set(), "NEUTRAL", "N/A"), None
                        )
                    )
                self.result_text.insert(tk.END,
                                        f"Piano di Breeding Ottimale Trovato (Costo: {total_cost_str} acquisti):\n")
                self.result_text.insert(tk.END, "=" * 70 + "\n")

                if not plan_steps_for_display or \
                        (hasattr(plan_steps_for_display[0].child, 'name') and plan_steps_for_display[
                            0].child.name.startswith("Errore") and \
                         "Ricostr. Fallita" in plan_steps_for_display[0].child.source_info):
                    self.result_text.insert(tk.END,
                                            "Ricostruzione del piano fallita o piano vuoto restituito dall'algoritmo.\n")
                else:
                    for step in plan_steps_for_display:
                        self.result_text.insert(tk.END, str(step) + "\n")
            else:
                self.result_text.insert(tk.END,
                                        "Nessun piano di breeding trovato con i parametri forniti o entro i limiti di ricerca.\n")
        except Exception as e:
            self.result_text.delete('1.0', tk.END)
            messagebox.showerror("Errore Esecuzione A*", f"Si è verificato un errore: {str(e)}")
            self.result_text.insert(tk.END, f"Errore durante l'esecuzione dell'algoritmo A*:\n{str(e)}\n\n")
            import traceback
            self.result_text.insert(tk.END, traceback.format_exc())
        finally:
            self._make_text_readonly_selectable(self.result_text)

    def _create_inventory_tab(self, tab: ttk.Frame):
        add_frame = ttk.LabelFrame(tab, text="Aggiungi un Pokémon che possiedi", padding=10)
        add_frame.pack(fill=tk.X, pady=5, padx=5)
        ttk.Label(add_frame, text="Specie:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.inv_species_var = tk.StringVar()
        self.inv_species_entry = ttk.Entry(add_frame, textvariable=self.inv_species_var, width=30)
        self.inv_species_entry.grid(row=0, column=1, sticky="ew", padx=5)
        self.inv_species_entry.bind("<KeyRelease>", lambda e: self._on_species_entry_keyup(e, self.inv_species_var,
                                                                                           self.inv_species_entry))
        self.inv_species_entry.bind("<Down>", lambda e: self._handle_entry_down_arrow(self.inv_species_entry))
        ttk.Label(add_frame, text="Nome (Opz.):").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.inv_name_var = tk.StringVar()
        ttk.Entry(add_frame, textvariable=self.inv_name_var, width=30).grid(row=1, column=1, sticky="ew", padx=5)
        inv_natures = ["NEUTRAL"] + core.ALL_NATURES
        ttk.Label(add_frame, text="Natura:").grid(row=2, column=0, sticky="w", padx=5, pady=5)
        self.inv_nature_var = tk.StringVar(value="NEUTRAL")
        ttk.Combobox(add_frame, textvariable=self.inv_nature_var, values=inv_natures, state="readonly", width=28).grid(
            row=2, column=1, sticky="ew", padx=5)
        inv_genders = ["Maschio", "Femmina", "Genderless"]
        ttk.Label(add_frame, text="Sesso:").grid(row=3, column=0, sticky="w", padx=5, pady=5)
        self.inv_gender_var = tk.StringVar(value="Maschio")
        ttk.Combobox(add_frame, textvariable=self.inv_gender_var, values=inv_genders, state="readonly", width=28).grid(
            row=3, column=1, sticky="ew", padx=5)
        inv_iv_frame = ttk.LabelFrame(add_frame, text="IVs a 31")
        inv_iv_frame.grid(row=0, column=2, rowspan=4, padx=10, pady=5, sticky="ns")
        self.inv_iv_vars = {stat: tk.BooleanVar() for stat in core.IV_STATS}
        for stat in core.IV_STATS: ttk.Checkbutton(inv_iv_frame, text=stat, variable=self.inv_iv_vars[stat]).pack(
            anchor="w", padx=5, pady=2)
        add_frame.columnconfigure(1, weight=1)
        add_button = ttk.Button(add_frame, text="Aggiungi a Inventario", command=self._add_to_inventory)
        add_button.grid(row=4, column=0, columnspan=3, pady=15)
        view_frame = ttk.LabelFrame(tab, text="Mio Inventario", padding="10")
        view_frame.pack(fill=tk.BOTH, expand=True, pady=5, padx=5)
        self.inventory_text_widget = scrolledtext.ScrolledText(view_frame, wrap=tk.WORD, height=10)
        self.inventory_text_widget.pack(fill=tk.BOTH, expand=True)
        self._make_text_readonly_selectable(self.inventory_text_widget)

    def _add_to_inventory(self):
        self._hide_autocomplete(refocus_entry=False)
        species_input = self.inv_species_var.get()
        if not species_input: messagebox.showerror("Errore Input", "La specie è richiesta."); return
        species = species_input.capitalize()
        if species.lower() not in core.POKEMON_EGG_GROUPS_RAW and species.lower() != "ditto":
            messagebox.showwarning("Specie Sconosciuta", f"Specie '{species}' non nei dati.")
        ivs = {stat for stat, var in self.inv_iv_vars.items() if var.get()}
        new_pokemon = core.Pokemon(species=species, name=self.inv_name_var.get() or species,
                                   nature=self.inv_nature_var.get(), gender=self.inv_gender_var.get(), ivs=ivs,
                                   is_owned=True, source_info="Posseduto")
        self.user_inventory.append(new_pokemon)
        self._update_inventory_display()
        self.inv_species_var.set("");
        self.inv_name_var.set("");
        self.inv_nature_var.set("NEUTRAL")
        self.inv_gender_var.set("Maschio");
        [var.set(False) for var in self.inv_iv_vars.values()]
        messagebox.showinfo("Inventario Aggiornato", f"{new_pokemon.name} aggiunto.")

    def _update_inventory_display(self):
        self.inventory_text_widget.config(state=tk.NORMAL)
        self.inventory_text_widget.delete('1.0', tk.END)
        if not self.user_inventory:
            self.inventory_text_widget.insert(tk.END, "Inventario vuoto.")
        else:
            for i, pkm in enumerate(self.user_inventory):
                self.inventory_text_widget.insert(tk.END, f"{i + 1}. {pkm.get_display_string()} (ID: {pkm.id})\n")
        self._make_text_readonly_selectable(self.inventory_text_widget)


if __name__ == "__main__":
    app_root = tk.Tk()
    gui = BreedingPlannerGUI_v8(app_root)
    app_root.mainloop()
