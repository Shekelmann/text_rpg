"""Reusable floating inventory UI; item rules remain in domain classes."""

import tkinter as tk

from item_presenter import item_icon_path, item_tooltip_lines


BG = "#101314"
PANEL = "#1c211f"
SLOT_BG = "#121715"
SLOT_EDGE = "#554e3b"
INK = "#ded8c5"
MUTED = "#a8ad9e"
GOLD = "#b8a16c"
RARITY_EDGES = {
    "COMMON": "#777b78",
    "RARE": "#668ed0",
    "EPIC": "#a36bd0",
    "LEGENDARY": "#c58b49",
}


class FloatingWindow(tk.Toplevel):
    """Small borderless window with a reusable draggable title area."""

    def __init__(self, master, title, on_close=None, anchor=None, position=None, on_position=None):
        super().__init__(master, bg=SLOT_EDGE)
        self.withdraw()
        self.anchor = anchor or master
        self.saved_position = position
        self.on_position = on_position
        self._on_close = on_close
        self._drag_origin = None
        self.overrideredirect(True)
        self.transient(master)
        try:
            self.attributes("-topmost", True)
        except tk.TclError:
            pass

        surface = tk.Frame(self, bg=PANEL, highlightthickness=1,
                           highlightbackground=SLOT_EDGE)
        surface.pack(fill="both", expand=True, padx=1, pady=1)
        self.title_bar = tk.Frame(surface, bg="#272d29", height=34, cursor="fleur")
        self.title_bar.pack(fill="x")
        self.title_bar.pack_propagate(False)
        self.title_label = tk.Label(
            self.title_bar, text=title, bg="#272d29", fg=GOLD,
            font=("Georgia", 11, "bold"), anchor="w", padx=10,
        )
        self.title_label.pack(side="left", fill="both", expand=True)
        close = tk.Button(
            self.title_bar, text="×", command=self.close, bg="#272d29", fg=INK,
            activebackground="#6b3333", activeforeground="#ffffff",
            relief="flat", borderwidth=0, font=("Segoe UI", 13), width=3,
        )
        close.pack(side="right", fill="y")
        self.content = tk.Frame(surface, bg=PANEL, padx=10, pady=10)
        self.content.pack(fill="both", expand=True)

        for widget in (self.title_bar, self.title_label):
            widget.bind("<ButtonPress-1>", self._start_drag)
            widget.bind("<B1-Motion>", self._drag)
        self.bind("<Escape>", lambda _event: self.close())

    def place_over_master(self):
        self.update_idletasks()
        if self.saved_position is None:
            x = self.anchor.winfo_rootx() + (self.anchor.winfo_width() - self.winfo_reqwidth()) // 2
            y = self.anchor.winfo_rooty() + (self.anchor.winfo_height() - self.winfo_reqheight()) // 2
        else:
            x = self.master.winfo_rootx() + self.saved_position[0]
            y = self.master.winfo_rooty() + self.saved_position[1]
        self._place(x, y)
        self.deiconify()
        self.lift()

    def _place(self, x, y):
        left, top = self.master.winfo_rootx(), self.master.winfo_rooty()
        x = max(left, min(x, left + max(0, self.master.winfo_width() - self.winfo_reqwidth())))
        y = max(top, min(y, top + max(0, self.master.winfo_height() - self.winfo_reqheight())))
        self.geometry(f"+{x}+{y}")
        if self.on_position:
            self.on_position((x - left, y - top))

    def _start_drag(self, event):
        self._drag_origin = (event.x_root - self.winfo_x(), event.y_root - self.winfo_y())

    def _drag(self, event):
        if self._drag_origin is None:
            return
        x = event.x_root - self._drag_origin[0]
        y = event.y_root - self._drag_origin[1]
        self._place(x, y)

    def close(self):
        if not self.winfo_exists():
            return
        callback, self._on_close = self._on_close, None
        if self.on_position:
            self.on_position((self.winfo_x() - self.master.winfo_rootx(),
                              self.winfo_y() - self.master.winfo_rooty()))
        self.destroy()
        if callback is not None:
            callback()


class DelayedTooltip:
    """One delayed tooltip controller shared by every slot in a window."""

    def __init__(self, owner, delay_ms=1000):
        self.owner = owner
        self.delay_ms = delay_ms
        self.pending = None
        self.window = None
        self._token = None

    def enter(self, token, lines):
        self.hide()
        self._token = token
        self.pending = self.owner.after(
            self.delay_ms,
            lambda: self._show(token, tuple(lines)),
        )

    def bind_to(self, widget, lines):
        widget.bind("<Enter>", lambda e: self.enter(widget, lines() if callable(lines) else lines))
        widget.bind("<Leave>", lambda e: self.leave())
        widget.bind("<ButtonPress>", lambda e: self.hide(), add="+")

    def leave(self):
        self.hide()

    def hide(self):
        if self.pending is not None:
            try:
                self.owner.after_cancel(self.pending)
            except tk.TclError:
                pass
            self.pending = None
        if self.window is not None:
            try:
                self.window.destroy()
            except tk.TclError:
                pass
            self.window = None
        self._token = None

    def _show(self, token, lines):
        self.pending = None
        if token is not self._token or not lines or not self.owner.winfo_exists():
            return
        window = tk.Toplevel(self.owner, bg=SLOT_EDGE)
        window.overrideredirect(True)
        try:
            window.attributes("-topmost", True)
        except tk.TclError:
            pass
        tk.Label(
            window, text="\n".join(lines), justify="left", anchor="w",
            bg="#171b19", fg=INK, padx=10, pady=8,
            font=("Segoe UI", 9), highlightthickness=1,
            highlightbackground=SLOT_EDGE,
        ).pack()
        window.update_idletasks()
        x, y = self.owner.winfo_pointerx() + 16, self.owner.winfo_pointery() + 18
        width, height = window.winfo_reqwidth(), window.winfo_reqheight()
        screen_width = window.winfo_screenwidth()
        screen_height = window.winfo_screenheight()
        x = max(0, min(x, screen_width - width - 4))
        y = max(0, min(y, screen_height - height - 4))
        window.geometry(f"+{x}+{y}")
        self.window = window


class InventoryWindow(FloatingWindow):
    COLUMNS = 5
    ROWS = 4
    SLOT_SIZE = 70

    def __init__(self, master, player, on_change=None, on_close=None, **placement):
        super().__init__(master, "РЮКЗАК", on_close=on_close, **placement)
        self.player = player
        self.inventory = player.inventory
        self.on_change = on_change
        self.drag_source = None
        self.slot_widgets = []
        self.image_cache = {}
        self.tooltip = DelayedTooltip(self, delay_ms=1000)

        toolbar = tk.Frame(self.content, bg=PANEL)
        toolbar.pack(fill="x", pady=(0, 8))
        self.counter = tk.Label(toolbar, text="", bg=PANEL, fg=MUTED,
                                font=("Segoe UI", 9), anchor="w")
        self.counter.pack(side="left", fill="x", expand=True)
        self.sort_button = tk.Button(
            toolbar, text="Сортировать", command=self.sort_items,
            bg="#2b322a", fg=INK, activebackground="#424936",
            activeforeground="#f1e5bf", relief="flat", borderwidth=0,
            padx=9, pady=4, font=("Segoe UI", 9),
        )
        self.sort_button.pack(side="right")
        self.tooltip.bind_to(self.sort_button, (
            "Сортировка инвентаря",
            "Сначала оружие, затем броня, зелья и остальные предметы.",
            "Внутри типа: LEGENDARY → EPIC → RARE → COMMON.",
            "При одинаковой редкости — по названию, без учёта регистра.",
            "Пустые ячейки перемещаются в конец.",
        ))

        grid = tk.Frame(self.content, bg=PANEL)
        grid.pack()
        for index in range(self.inventory.size):
            holder = tk.Frame(
                grid, width=self.SLOT_SIZE, height=self.SLOT_SIZE,
                bg=SLOT_BG, highlightthickness=1,
                highlightbackground=SLOT_EDGE,
            )
            holder.grid(
                row=index // self.COLUMNS,
                column=index % self.COLUMNS,
                padx=2, pady=2,
            )
            holder.grid_propagate(False)
            holder.inventory_slot = index
            slot = tk.Label(
                holder, text="", bg=SLOT_BG, fg=MUTED,
                font=("Segoe UI", 9, "bold"), cursor="hand2",
            )
            slot.place(x=2, y=2, width=self.SLOT_SIZE - 4, height=self.SLOT_SIZE - 4)
            slot.inventory_slot = index
            slot.bind("<ButtonPress-1>", self._start_item_drag)
            slot.bind("<ButtonRelease-1>", self._finish_item_drag)
            slot.bind("<Double-Button-1>", lambda _event, i=index: self.equip_slot(i))
            slot.bind("<Enter>", lambda _event, i=index: self._tooltip_enter(i))
            slot.bind("<Leave>", lambda _event: self.tooltip.leave())
            self.slot_widgets.append((holder, slot))

        self.status = tk.Label(
            self.content,
            text="Перетаскивание — переместить · двойной клик — экипировать",
            bg=PANEL, fg=MUTED, font=("Segoe UI", 8), anchor="w",
        )
        self.status.pack(fill="x", pady=(8, 0))
        self.refresh()
        self.place_over_master()

    def refresh(self):
        self.tooltip.hide()
        self.counter.configure(
            text=f"Занято {len(self.inventory.items)} / {self.inventory.size}"
        )
        for index, (holder, slot) in enumerate(self.slot_widgets):
            item = self.inventory.item_at(index)
            image = self._load_image(item)
            if item is None:
                text, edge = "", SLOT_EDGE
            else:
                text = "" if image else "?"
                rarity = getattr(getattr(item, "rarity", None), "name", "COMMON")
                edge = RARITY_EDGES.get(rarity, SLOT_EDGE)
            holder.configure(highlightbackground=edge)
            slot.configure(image=image or "", text=text)
            slot.image = image

    def sort_items(self):
        self.inventory.sort_items()
        self.status.configure(text="Предметы отсортированы.")
        self.refresh()
        self._changed()

    def move_item(self, source_slot, target_slot):
        moved = self.inventory.move_item(source_slot, target_slot)
        if moved:
            self.status.configure(text="Расположение сохранено.")
            self.refresh()
            self._changed()
        return moved

    def equip_slot(self, slot):
        item = self.inventory.item_at(slot)
        if item is None:
            return False
        if getattr(item, "is_weapon", False):
            equipped = self.player.equip_weapon(item)
        elif getattr(item, "item_type", None) == "armor":
            equipped = self.player.equip_armor(item)
        else:
            self.status.configure(text="Этот предмет нельзя экипировать.")
            return False
        self.status.configure(
            text=(f"Экипировано: {item.name}." if equipped
                  else f"Не удалось экипировать: {item.name}.")
        )
        if equipped:
            self.refresh()
            self._changed()
        return equipped

    def _load_image(self, item):
        if item is None:
            return None
        path = item_icon_path(item)
        if path is None:
            return None
        key = str(path)
        if key not in self.image_cache:
            try:
                self.image_cache[key] = tk.PhotoImage(master=self, file=key)
            except (tk.TclError, OSError):
                self.image_cache[key] = None
        return self.image_cache[key]

    def _tooltip_enter(self, slot):
        item = self.inventory.item_at(slot)
        if item is not None:
            self.tooltip.enter(item, item_tooltip_lines(item))

    def _start_item_drag(self, event):
        slot = event.widget.inventory_slot
        self.drag_source = slot if self.inventory.item_at(slot) is not None else None
        self.tooltip.hide()

    def _finish_item_drag(self, event):
        source, self.drag_source = self.drag_source, None
        if source is None:
            return
        target_widget = self.winfo_containing(event.x_root, event.y_root)
        while target_widget is not None and not hasattr(target_widget, "inventory_slot"):
            target_widget = getattr(target_widget, "master", None)
        if target_widget is not None:
            self.move_item(source, target_widget.inventory_slot)

    def _changed(self):
        if self.on_change is not None:
            self.on_change()

    def close(self):
        if hasattr(self, "tooltip"):
            self.tooltip.hide()
        super().close()
