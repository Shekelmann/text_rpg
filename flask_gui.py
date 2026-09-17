"""Souls-style permanent flask allocation window."""

import tkinter as tk

from inventory_gui import FloatingWindow, GOLD, INK, MUTED, PANEL, SLOT_BG, SLOT_EDGE


class FlaskAllocationWindow(FloatingWindow):
    def __init__(self, master, total, hp, on_result, **placement):
        self.total = total
        self.hp = hp
        self.on_result = on_result
        super().__init__(
            master,
            "РАСПРЕДЕЛЕНИЕ ФЛЯГ",
            on_close=lambda: self._finish(None),
            **placement,
        )
        tk.Label(
            self.content,
            text=f"Общий запас: {total}",
            bg=PANEL,
            fg=GOLD,
            font=("Segoe UI", 11, "bold"),
        ).pack(pady=(0, 10))

        row = tk.Frame(self.content, bg=PANEL)
        row.pack(fill="both", expand=True)
        self.count_labels = {}
        self.buttons = {}
        self._build_side(row, "hp", "HP-фляги", "#b44848", 0)
        self._build_side(row, "mp", "MP-фляги", "#4a80b6", 1)

        actions = tk.Frame(self.content, bg=PANEL)
        actions.pack(fill="x", pady=(12, 0))
        tk.Button(
            actions, text="Применить", command=lambda: self._finish(self.hp),
            bg="#354433", fg=INK, activebackground="#4b6248",
            relief="flat", padx=12, pady=7,
        ).pack(side="left", fill="x", expand=True, padx=(0, 4))
        tk.Button(
            actions, text="Отмена", command=self.close,
            bg="#322d2b", fg=INK, activebackground="#51433e",
            relief="flat", padx=12, pady=7,
        ).pack(side="left", fill="x", expand=True, padx=(4, 0))
        self._refresh()
        self.place_over_master()

    def _build_side(self, parent, resource, title, color, column):
        frame = tk.Frame(
            parent, bg=SLOT_BG, highlightthickness=1,
            highlightbackground=SLOT_EDGE, padx=14, pady=10,
        )
        frame.grid(row=0, column=column, sticky="nsew", padx=4)
        parent.columnconfigure(column, weight=1)
        tk.Label(frame, text=title, bg=SLOT_BG, fg=INK,
                 font=("Segoe UI", 10, "bold")).pack()
        icon = tk.Canvas(frame, width=72, height=64, bg=SLOT_BG, highlightthickness=0)
        icon.pack(pady=5)
        icon.create_polygon(
            29, 7, 43, 7, 43, 20, 53, 29, 53, 50,
            19, 50, 19, 29, 29, 20,
            fill="#343d39", outline=GOLD, width=1,
        )
        icon.create_rectangle(23, 32, 49, 46, fill=color, outline="")
        icon.create_rectangle(28, 4, 44, 10, fill=GOLD, outline="")

        controls = tk.Frame(frame, bg=SLOT_BG)
        controls.pack()
        decrease = tk.Button(
            controls, text="◀", command=lambda r=resource: self._adjust(r, -1),
            bg=PANEL, fg=INK, disabledforeground=MUTED, relief="flat", width=3,
        )
        decrease.pack(side="left")
        count = tk.Label(controls, text="0", bg=SLOT_BG, fg=GOLD,
                         font=("Consolas", 16, "bold"), width=3)
        count.pack(side="left", padx=4)
        increase = tk.Button(
            controls, text="▶", command=lambda r=resource: self._adjust(r, 1),
            bg=PANEL, fg=INK, disabledforeground=MUTED, relief="flat", width=3,
        )
        increase.pack(side="left")
        self.count_labels[resource] = count
        self.buttons[(resource, -1)] = decrease
        self.buttons[(resource, 1)] = increase

    @property
    def mp(self):
        return self.total - self.hp

    def _adjust(self, resource, delta):
        hp_delta = delta if resource == "hp" else -delta
        candidate = self.hp + hp_delta
        if 0 <= candidate <= self.total:
            self.hp = candidate
            self._refresh()

    def _refresh(self):
        self.count_labels["hp"].configure(text=str(self.hp))
        self.count_labels["mp"].configure(text=str(self.mp))
        self.buttons[("hp", -1)].configure(state="normal" if self.hp > 0 else "disabled")
        self.buttons[("hp", 1)].configure(state="normal" if self.hp < self.total else "disabled")
        self.buttons[("mp", -1)].configure(state="normal" if self.mp > 0 else "disabled")
        self.buttons[("mp", 1)].configure(state="normal" if self.mp < self.total else "disabled")

    def _finish(self, result):
        callback, self.on_result = self.on_result, None
        self._on_close = None
        if self.winfo_exists():
            self.destroy()
        if callback is not None:
            callback(result)
