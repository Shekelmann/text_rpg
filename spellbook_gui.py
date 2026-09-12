"""Read-only spellbook window. Receives view data, never domain objects."""
import tkinter as tk
from tkinter import ttk

from inventory_gui import FloatingWindow, PANEL, SLOT_BG, INK, MUTED, GOLD


class SpellBookWindow(FloatingWindow):
    def __init__(self, master, data, **kwargs):
        super().__init__(master, "Книга заклинаний", **kwargs)
        self.data = {}
        style = ttk.Style(self)
        style.configure("SpellBook.TNotebook", background=PANEL, borderwidth=0)
        style.configure(
            "SpellBook.TNotebook.Tab", background=SLOT_BG, foreground=MUTED,
            padding=(12, 6), font=("Segoe UI", 10),
        )
        style.map(
            "SpellBook.TNotebook.Tab",
            background=[("selected", "#424936"), ("active", "#30382f")],
            foreground=[("selected", GOLD), ("!selected", MUTED)],
            padding=[("selected", (18, 10)), ("!selected", (12, 6))],
            font=[("selected", ("Segoe UI", 11, "bold")),
                  ("!selected", ("Segoe UI", 10))],
        )
        self.notebook = ttk.Notebook(self.content, style="SpellBook.TNotebook")
        self.notebook.pack(fill="both", expand=True)
        self.lists = {}
        self.empty_labels = {}
        self.keys = ("learned", "scrolls")
        for key, title in zip(self.keys, ("Постоянные", "Одноразовые")):
            page = tk.Frame(self.notebook, bg=PANEL)
            self.notebook.add(page, text=title)
            empty = tk.Label(page, text="", bg=PANEL, fg=MUTED, anchor="w")
            empty.pack(fill="x", padx=6, pady=6)
            self.empty_labels[key] = empty
            row = tk.Frame(page, bg=PANEL)
            row.pack(fill="both", expand=True)
            listing = tk.Listbox(row, bg=SLOT_BG, fg=INK, selectbackground="#424936",
                                 selectforeground=INK, exportselection=False,
                                 font=("Segoe UI", 11), height=8, width=58,
                                 highlightthickness=0)
            listing.pack(side="left", fill="both", expand=True)
            scrollbar = ttk.Scrollbar(row, command=listing.yview)
            scrollbar.pack(side="right", fill="y")
            listing.configure(yscrollcommand=scrollbar.set)
            listing.bind("<<ListboxSelect>>", self.show_selected)
            self.lists[key] = listing
        self.details = tk.Text(self.content, bg=SLOT_BG, fg=INK, font=("Segoe UI", 10),
                               width=62, height=9, wrap="word", relief="flat", padx=8, pady=8)
        self.details.pack(fill="both", expand=True, pady=(10, 4))
        tk.Label(self.content, text="В бою используйте действие «Заклинание».",
                 bg=PANEL, fg=GOLD, anchor="w").pack(fill="x")
        self.notebook.bind("<<NotebookTabChanged>>", self.show_selected)
        self.refresh(data)
        self.place_over_master()

    def refresh(self, data):
        for key, listing in self.lists.items():
            selection = listing.curselection()
            old = self.data.get(key, ())
            selected_id = old[selection[0]]["id"] if selection and selection[0] < len(old) else None
            listing.delete(0, "end")
            entries = data.get(key, ())
            for entry in entries:
                suffix = f" ×{entry['count']}" if key == "scrolls" else ""
                listing.insert("end", entry["name"] + suffix)
            self.empty_labels[key].configure(text=("Изученные заклинания" if key == "learned" else "Свитки")
                                              if entries else ("Нет изученных заклинаний." if key == "learned" else "Нет одноразовых заклинаний."))
            if entries:
                index = next((i for i, entry in enumerate(entries) if entry["id"] == selected_id), 0)
                listing.selection_set(index)
        self.data = data
        self.show_selected()

    def show_selected(self, event=None):
        key = self.keys[self.notebook.index(self.notebook.select())]
        selection = self.lists[key].curselection()
        entries = self.data.get(key, ())
        text = "Выберите заклинание." if entries else self.empty_labels[key].cget("text")
        if selection and selection[0] < len(entries):
            entry = entries[selection[0]]
            text = entry["details"]
            if key == "scrolls":
                text += f"\nКоличество: {entry['count']}"
        self.details.configure(state="normal")
        self.details.delete("1.0", "end")
        self.details.insert("1.0", text)
        self.details.configure(state="disabled")
