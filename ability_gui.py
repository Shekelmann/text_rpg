"""Out-of-combat ability loadout window."""

import tkinter as tk

from gui_views import ability_snapshot
from inventory_gui import BG, PANEL, SLOT_BG, SLOT_EDGE, INK, MUTED, GOLD


class AbilityWindow(tk.Toplevel):
    def __init__(self, master, player, on_change=None, on_close=None):
        super().__init__(master)
        self.player = player
        self.on_change = on_change
        self.on_close = on_close
        self.title("Способности")
        self.geometry("650x470")
        self.minsize(560, 400)
        self.configure(bg=BG)
        self.protocol("WM_DELETE_WINDOW", self.close)

        tk.Label(
            self, text="СПОСОБНОСТИ", bg=BG, fg=GOLD,
            font=("Georgia", 16, "bold"),
        ).pack(anchor="w", padx=16, pady=(14, 8))
        self.slot_frame = tk.Frame(self, bg=BG)
        self.slot_frame.pack(fill="x", padx=12, pady=(0, 10))
        self.list_frame = tk.Frame(self, bg=BG)
        self.list_frame.pack(fill="both", expand=True, padx=12, pady=(0, 12))
        self.status = tk.Label(
            self, text="", bg=BG, fg=MUTED, anchor="w",
            font=("Segoe UI", 9),
        )
        self.status.pack(fill="x", padx=16, pady=(0, 10))
        self.refresh()

    def refresh(self):
        data = ability_snapshot(self.player)
        for parent in (self.slot_frame, self.list_frame):
            for child in parent.winfo_children():
                child.destroy()

        for index, entry in enumerate(data["slots"]):
            frame = tk.Frame(
                self.slot_frame, bg=SLOT_BG, highlightthickness=1,
                highlightbackground=SLOT_EDGE,
            )
            frame.pack(side="left", fill="x", expand=True, padx=4)
            tk.Label(
                frame,
                text=f"Слот {index + 1}\n{entry['name'] if entry else 'Пусто'}",
                bg=SLOT_BG, fg=INK if entry else MUTED,
                justify="left", font=("Segoe UI", 9, "bold"),
            ).pack(side="left", fill="both", expand=True, padx=8, pady=8)
            tk.Button(
                frame, text="Снять", relief="flat", bg=PANEL, fg=INK,
                disabledforeground=MUTED,
                state="normal" if entry else "disabled",
                command=lambda i=index: self._unequip(i),
            ).pack(side="right", padx=6, pady=8)

        available = data["available"]
        if not available:
            tk.Label(
                self.list_frame,
                text="Для текущего класса пока нет доступных способностей.",
                bg=BG, fg=MUTED, font=("Segoe UI", 10),
            ).pack(anchor="w", padx=6, pady=12)
            return

        for entry in available:
            card = tk.Frame(
                self.list_frame, bg=PANEL, highlightthickness=1,
                highlightbackground=SLOT_EDGE,
            )
            card.pack(fill="x", pady=4)
            details = (
                f"{entry['name']}\n{entry['description']}\n"
                f"Стоимость: {entry['action_point_cost']} ОД   ·   "
                f"Перезарядка: {entry['cooldown']} хода\n"
                f"Статус: {'экипирована' if entry['equipped'] else 'не экипирована'}"
            )
            tk.Label(
                card, text=details, bg=PANEL, fg=INK, justify="left",
                anchor="w", wraplength=360, font=("Segoe UI", 10),
            ).pack(side="left", fill="both", expand=True, padx=10, pady=8)
            buttons = tk.Frame(card, bg=PANEL)
            buttons.pack(side="right", padx=6, pady=6)
            for index in range(3):
                tk.Button(
                    buttons, text=f"В слот {index + 1}", relief="flat",
                    bg=SLOT_BG, fg=INK,
                    command=lambda ability_id=entry["id"], i=index:
                        self._equip(ability_id, i),
                ).pack(fill="x", pady=1)

    def _equip(self, ability_id, slot_index):
        changed = self.player.equip_ability(ability_id, slot_index)
        self.status.configure(
            text="Способность экипирована." if changed else
                 "Не удалось экипировать способность."
        )
        if changed and self.on_change:
            self.on_change()
        self.refresh()

    def _unequip(self, slot_index):
        changed = self.player.unequip_ability(slot_index)
        self.status.configure(
            text="Способность снята." if changed else "Слот уже пуст."
        )
        if changed and self.on_change:
            self.on_change()
        self.refresh()

    def close(self):
        if self.on_close:
            self.on_close()
        self.destroy()

