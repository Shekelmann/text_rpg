"""Read-only character and future ability panels, using shared item tooltips."""

import tkinter as tk
from inventory_gui import DelayedTooltip, PANEL, SLOT_BG, SLOT_EDGE, INK, MUTED, GOLD


class CharacterPanel(tk.Frame):
    def __init__(self, master):
        super().__init__(master, bg=PANEL)
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=2)
        self.tooltip = DelayedTooltip(self)
        self.images = {}
        self.stats = tk.Label(self, bg=PANEL, fg=INK, justify="left", anchor="nw", font=("Segoe UI", 10))
        self.stats.grid(row=0, column=0, sticky="nsew", padx=12, pady=12)
        self.slots = tk.Frame(self, bg=PANEL)
        self.slots.grid(row=0, column=1, sticky="nsew", padx=8, pady=8)
        for i in range(2):
            self.slots.columnconfigure(i, weight=1)
        self.slot_widgets = {}

    def refresh(self, data):
        self.tooltip.hide()
        self.stats.configure(text=(f"{data['name']}\n{data['class']}\nУровень {data['level']}\n\n"
            f"STR / Сила: {data['strength']}\nDEX / Ловкость: {data['dexterity']}\nINT / Интеллект: {data['intelligence']}\n\n"
            f"HP: {data['health']} / {data['max_health']}\nMP: {data['mana']} / {data['max_mana']}\n"
            f"Броня: {data['armor']}\nУрон: {data['damage']}\nЗолото: {data['gold']}\n"
            f"Опыт: {data['exp']} / {data['exp_to_level']}\nСвободные очки: {data['unspent']}"))
        for child in self.slots.winfo_children():
            child.destroy()
        self.slot_widgets.clear()
        for i, entry in enumerate(data['equipment_slots']):
            frame = tk.Frame(self.slots, bg=SLOT_BG, highlightthickness=1, highlightbackground=SLOT_EDGE)
            frame.grid(row=i // 2, column=i % 2, sticky="nsew", padx=3, pady=3)
            image = None
            path = entry['icon']
            if path:
                if path not in self.images:
                    try:
                        self.images[path] = tk.PhotoImage(master=self, file=path)
                    except (OSError, tk.TclError):
                        self.images[path] = None
                image = self.images[path]
            picture = tk.Label(frame, bg=SLOT_BG, fg=MUTED, image=image or "",
                               text="◇" if entry['future'] else (("?" if entry['name'] != "—" else "—") if not image else ""), width=0)
            picture.pack(side="left", padx=4, pady=4)
            label = tk.Label(frame, text=entry['label'] + "\n" + ("Позже" if entry['future'] else entry['name']),
                             bg=SLOT_BG, fg=INK, justify="left", anchor="w", wraplength=110, font=("Segoe UI", 9))
            label.pack(side="left", fill="both", expand=True, padx=3)
            for widget in (frame, picture, label):
                self.tooltip.bind_to(widget, entry['tooltip'])
            self.slot_widgets[entry['id']] = frame

    def hide(self):
        self.tooltip.hide()
        self.grid_remove()


class AbilityPanel(tk.Frame):
    def __init__(self, master, on_use=None):
        super().__init__(master, bg=PANEL, highlightthickness=1, highlightbackground=SLOT_EDGE)
        self.on_use = on_use
        self.context_allowed = False
        self.enabled = {}
        self.tooltip = DelayedTooltip(self)
        self.skill_slots = []
        skills = tk.Frame(self, bg=PANEL)
        skills.pack(side="left", fill="both", expand=True, padx=6, pady=4)
        tk.Label(skills, text="НАВЫКИ / МАГИЯ · ПОЗЖЕ", bg=PANEL, fg=MUTED, font=("Segoe UI", 8)).pack(anchor="w")
        row = tk.Frame(skills, bg=PANEL)
        row.pack(fill="x")
        for i in range(4):
            slot = tk.Button(row, text=str(i + 1), bg=SLOT_BG, disabledforeground=MUTED,
                             state="disabled", relief="flat", width=3)
            slot.pack(side="left", fill="x", expand=True, padx=2, pady=2)
            self.skill_slots.append(slot)
        self.flask_widgets = {}
        self.data = {}
        for key, color in (("hp", "#b44848"), ("mp", "#4a80b6")):
            slot = tk.Canvas(self, bg=SLOT_BG, width=72, height=62, highlightthickness=1, highlightbackground=SLOT_EDGE)
            slot.pack(side="left", padx=4, pady=4)
            # Crisp code-native bottle pictogram: no bitmap interpolation.
            slot.create_polygon(29, 8, 42, 8, 42, 20, 51, 28, 51, 43, 21, 43, 21, 28, 29, 20,
                                fill="#343d39", outline=GOLD, width=1)
            slot.create_rectangle(24, 30, 48, 40, fill=color, outline="")
            slot.create_rectangle(28, 5, 43, 10, fill=GOLD, outline="")
            count = slot.create_text(36, 53, text=f"{key.upper()} ×—", fill=INK, font=("Segoe UI", 9))
            self.flask_widgets[key] = (slot, count)
            self.tooltip.bind_to(slot, lambda k=key: self.flask_tooltip(k))
            slot.bind("<ButtonRelease-1>", lambda e, k=key: self.activate(k))

    def activate(self, key):
        if self.enabled.get(key) and self.on_use:
            self.on_use(key)

    def set_context(self, allowed):
        self.context_allowed = allowed
        for key, (widget, _) in self.flask_widgets.items():
            active = bool(allowed and self.data.get(key, {}).get('usable'))
            self.enabled[key] = active
            widget.configure(cursor="hand2" if active else "", highlightbackground=GOLD if active else SLOT_EDGE,
                             bg=SLOT_BG if active else "#292b29")

    def refresh(self, entries):
        self.data = {entry['id']: entry for entry in entries}
        for key, (widget, label) in self.flask_widgets.items():
            count = self.data.get(key, {}).get('count')
            widget.itemconfigure(label, text=f"{key.upper()} ×{count if count is not None else '—'}")
        self.set_context(self.context_allowed)

    def flask_tooltip(self, key):
        entry = self.data.get(key, {})
        resource = key.upper()
        amount = entry.get('amount')
        count = entry.get('count')
        return (entry.get('name', f"{resource} Flask"), f"Восстанавливает {resource}.",
                f"Восстановление: {amount} {resource}" if amount is not None else "Количество восстановления пока не задано системой.",
                f"Осталось: {count}" if count is not None else "Запас фласок пока не задан системой.",
                "Расходует одно действие расходника в бою.")
