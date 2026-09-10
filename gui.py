"""Tk desktop frontend. No game rules or domain state live in this module."""

from enemy_art import ENEMY_ART, ART_ROOT
from dataclasses import dataclass, replace
from pathlib import Path
import queue
import re
import threading
import traceback
import tkinter as tk
from tkinter import ttk

from game_io import use_backend
from gui_views import character_snapshot, map_snapshot
from inventory_gui import DelayedTooltip, InventoryWindow
from item_presenter import TOOLTIP_COLORS
from gui_panels import CharacterPanel, AbilityPanel
import textwrap


ANSI = re.compile(r"\x1b\[([0-9;]*)m")
MENU_LINE = re.compile(r"^\s*[║│]?\s*(\d+)\s*[.\-—–]\s+(.+?)\s*[║│]?\s*$")
COLORS = {
    "30": "#8c929c", "31": "#ff7272", "32": "#82ce90",
    "33": "#e9ca79", "34": "#7ca9ff", "35": "#cd91ee",
    "36": "#78cdd5", "37": "#e7e9ee",
    "90": "#a5aab4", "91": "#ff9292", "92": "#a4e8ac",
    "93": "#ffe09b", "94": "#a0c0ff", "95": "#e2b0ff",
    "96": "#9be5ec", "97": "#ffffff",
}

COMBAT_LOG_COLORS = {**TOOLTIP_COLORS, "defeat": TOOLTIP_COLORS["bleeding"]}
EFFECT_LOG_STYLES = (
    (re.compile(r"\bЯд\b", re.IGNORECASE), "poison"),
    (re.compile(r"\bКровотечение\b", re.IGNORECASE), "bleeding"),
    (re.compile(r"\bИссушение\b", re.IGNORECASE), "drain"),
)
DAMAGE_PHRASE = re.compile(
    r"\b(?P<amount>\d+)(?P<space>\s+)(?P<word>урон(?:а|у|ом|е)?)\b",
    re.IGNORECASE,
)
CRITICAL_WORD = re.compile(r"\b(?:крит\w*|удар\w*)\b", re.IGNORECASE)
DEFEAT_MESSAGE = re.compile(r"Вы проиграли бой\.?", re.IGNORECASE)
ENEMY_IMAGE_FILES = {key: ART_ROOT / spec["file"] for key, spec in ENEMY_ART.items()}


def combat_message_segments(message, critical_damage=False):
    """Return display-only text segments; combat messages stay unchanged."""
    if DEFEAT_MESSAGE.fullmatch(message.strip()):
        return ((message, "defeat"),)
    style = "critical" if critical_damage else None
    keyword_pattern = CRITICAL_WORD if "крит" in message.lower() else None
    if keyword_pattern is not None:
        style = "critical"
    else:
        for pattern, effect_style in EFFECT_LOG_STYLES:
            if pattern.search(message):
                keyword_pattern = pattern
                style = effect_style
                break
    if style is None:
        return ((message, None),)

    ranges = []
    if keyword_pattern is not None:
        ranges.extend((match.start(), match.end()) for match in keyword_pattern.finditer(message))
    if critical_damage or any(pattern.search(message) for pattern, _ in EFFECT_LOG_STYLES):
        for match in DAMAGE_PHRASE.finditer(message):
            ranges.append(match.span("amount"))
            ranges.append(match.span("word"))
    ranges.sort()

    segments = []
    position = 0
    for start, end in ranges:
        if start < position:
            continue
        if start > position:
            segments.append((message[position:start], None))
        segments.append((message[start:end], style))
        position = end
    if position < len(message):
        segments.append((message[position:], None))
    return tuple(segments)


def menu_choices(text):
    """Adapt current numbered menus, including lines inside ASCII panels.

    A repeated key starts a newer menu (e.g. battle redraws). Input and clear
    boundaries reset the captured text, so previous screens cannot leak actions.
    """
    choices = {}
    for line in ANSI.sub("", text).splitlines():
        match = MENU_LINE.match(line)
        if match:
            key, label = match.groups()
            if key in choices:
                choices.clear()
            choices[key] = label.strip()
    return tuple(choices.items())


@dataclass(frozen=True)
class Prompt:
    text: str
    kind: str
    choices: tuple
    default: str = ""
    body: str = ""


class GameClosed(Exception):
    """Cooperative shutdown at the next game I/O boundary."""


class DesktopIO:
    """Queue bridge: game runs sequentially, Tk runs on its main thread."""

    def __init__(self):
        self.events = queue.Queue()
        self.answers = queue.Queue()
        self.closed = threading.Event()
        self.pending_text = []
        self.player = None
        self.world = None
        self.view_choices = ()

    def _check_open(self):
        if self.closed.is_set():
            raise GameClosed()

    def write(self, text):
        self._check_open()
        self.pending_text.append(text)
        self.events.put(("text", text))

    def clear(self):
        self._check_open()
        self.pending_text.clear()
        self.view_choices = ()
        self.events.put(("clear", None))

    def read(self, prompt, *, kind="menu", choices=None, default=""):
        self._check_open()
        body = "".join(self.pending_text)
        options = tuple(choices) if choices is not None else (menu_choices(body) or self.view_choices)
        self.pending_text.clear()
        self.view_choices = ()
        self.snapshot()
        if kind == "return":
            if body.strip():
                self.events.put(("notice", body.strip()))
            return ""
        if kind in ("pause", "text", "number"):
            options = ()
        self.events.put(("prompt", Prompt(prompt, kind, options, default, body)))
        answer = self.answers.get()
        self._check_open()
        return answer

    def bind_state(self, player, world):
        self.player, self.world = player, world

    def snapshot(self):
        if self.player is not None:
            self.events.put(("character", character_snapshot(self.player)))
        if self.world is not None and self.player is not None:
            self.events.put(("map", map_snapshot(self.world, self.player)))

    def present(self, view, **data):
        self._check_open()
        self.player = data.get("player", self.player)
        self.world = data.get("world", self.world)
        self.snapshot()
        if view == "character":
            return
        self.pending_text.clear()
        if view == "location":
            location = self.world.locations[self.player.current_location]
            self.view_choices = tuple((str(i), label) for i, (_, label) in enumerate(data["options"], 1))
            screen = {
                "kind": "location", "title": location["name"],
                "body": location["description"],
                "routes": {action: str(i) for i, (action, _) in enumerate(data["options"], 1)},
            }
        elif view == "battle":
            enemy = data["enemy"]
            self.view_choices = menu_choices("\n".join(data["actions"]))
            screen = {
                "kind": "battle", "title": "Бой",
                "body": "",
                "enemy_name": enemy.name,
                "enemy_level": enemy.level,
                "enemy_health": enemy.health,
                "enemy_max_health": enemy.max_health,
                "enemy_image_id": getattr(enemy, "id", None),
                "messages": tuple(data["messages"]),
            }
        else:
            raise ValueError(f"Unknown presentation: {view}")
        self.events.put(("screen", screen))

    def close(self):
        self.closed.set()
        self.answers.put("")


BG = "#101314"
PANEL = "#1c211f"
INK = "#ded8c5"
MUTED = "#a8ad9e"
GOLD = "#b8a16c"
EDGE = "#554e3b"


class StonePanel(tk.Canvas):
    """Small vector border texture, with a quiet solid surface behind the text."""

    def __init__(self, master, **kwargs):
        super().__init__(master, bg=PANEL, highlightthickness=1,
                         highlightbackground=EDGE, **kwargs)
        self.content = tk.Frame(self, bg=PANEL)
        self.inner = self.create_window(10, 10, window=self.content, anchor="nw")
        self.bind("<Configure>", self.resize)

    def resize(self, event):
        self.delete("stone")
        for y in range(0, event.height, 7):
            shade = "#272c28" if y % 3 else "#141917"
            self.create_line(0, y, event.width, y + 5, fill=shade, tags="stone")
        self.create_rectangle(4, 4, event.width - 5, event.height - 5,
                              outline="#706044", tags="stone")
        self.tag_lower("stone")
        self.itemconfigure(self.inner, width=max(1, event.width - 20),
                           height=max(1, event.height - 20))


class GameWindow:
    def __init__(self, root, game=None):
        self.root = root
        self.io = DesktopIO()
        self.waiting = False
        self.prompt = None
        self.foreground = "37"
        self.ansi_tail = ""
        self.worker = None
        self.character = None
        self.map_data = ()
        self.routes = {}
        self.location_slots = {key: i for i, key in enumerate(("move", "description", "unequip", "hunt", "chest", "ground_loot"))}
        self.overlay = None
        self.inventory_window = None
        self.inventory_position = None
        self.notice = ""
        self.output = ""
        self.last_screen = {"kind": "menu", "title": "Новое приключение", "body": ""}
        root.title("Axe and Sword")
        root.geometry("1340x940")
        root.minsize(1040, 880)
        root.configure(bg=BG)
        root.protocol("WM_DELETE_WINDOW", self.close)
        self._style()

        outer = tk.Frame(root, bg=BG, padx=12, pady=12)
        outer.pack(fill="both", expand=True)
        outer.columnconfigure(1, weight=1)
        outer.rowconfigure(1, weight=1)
        tk.Label(outer, text="AXE  &  SWORD", bg=BG, fg=GOLD,
                 font=("Georgia", 19, "bold")).grid(row=0, column=0, columnspan=3, pady=(0, 12))

        self.left = StonePanel(outer, width=190)
        self.left.grid(row=1, column=0, sticky="nsew", padx=(0, 10))
        navigation = self.left.content
        self._label(navigation, "ПУТЕШЕСТВИЕ", GOLD).pack(anchor="w", pady=(10, 16))
        self.global_buttons = {}
        self.global_labels = {}
        for action, label in (("inventory", "Открыть инвентарь"), ("character", "Персонаж"),
                              ("map", "Карта"),
                              ("loot_filter", "Лут-фильтр"), ("exit", "Выйти из игры")):
            button = self._button(navigation, label, lambda a=action: self.global_action(a))
            button.pack(fill="x", pady=5)
            button.configure(state="disabled")
            self.global_buttons[action] = button
            self.global_labels[action] = label
        self._label(navigation, "Мышь — выбор действия", MUTED,
                    font=("Segoe UI", 9)).pack(side="bottom", anchor="w", pady=12)

        center = tk.Frame(outer, bg=BG)
        center.grid(row=1, column=1, sticky="nsew")
        center.columnconfigure(0, weight=1)
        center.rowconfigure(1, weight=1)
        self.title = tk.Label(center, text="Новое приключение", anchor="w", bg=BG,
                              fg=GOLD, font=("Georgia", 17))
        self.title.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        self.center = center
        stage = tk.Frame(center, bg=BG, highlightthickness=1, highlightbackground=EDGE)
        stage.grid(row=1, column=0, sticky="nsew")
        self.stage = stage
        stage.rowconfigure(0, weight=1)
        stage.columnconfigure(0, weight=1)
        self.text = tk.Text(stage, wrap="none", state="disabled", bg="#131a18", fg=INK,
                            font=("Consolas", 11), padx=20, pady=20, borderwidth=0,
                            selectbackground="#514c36", insertbackground=INK)
        self.text.grid(row=0, column=0, sticky="nsew")
        self.stage_vertical = ttk.Scrollbar(stage, command=self.text.yview)
        self.stage_vertical.grid(row=0, column=1, sticky="ns")
        self.stage_horizontal = ttk.Scrollbar(stage, orient="horizontal", command=self.text.xview)
        self.stage_horizontal.grid(row=1, column=0, sticky="ew")
        self.text.configure(yscrollcommand=self.stage_vertical.set, xscrollcommand=self.stage_horizontal.set)
        for code, color in COLORS.items():
            self.text.tag_configure(code, foreground=color)

        self.battle_stage = tk.Frame(stage, bg="#131a18", padx=30, pady=22)
        self.enemy_group = tk.Frame(self.battle_stage, bg="#131a18")
        self.enemy_group.place(relx=0.5, rely=0.5, anchor="center")
        self.enemy_group.columnconfigure(0, weight=1, minsize=360)
        self.enemy_name_label = tk.Label(
            self.enemy_group, text="", bg="#131a18", fg=INK,
            font=("Georgia", 14, "bold"), anchor="center",
        )
        self.enemy_name_label.grid(row=0, column=0, sticky="ew", pady=(2, 7))
        self.enemy_level_label = tk.Label(
            self.enemy_group, text="", bg="#131a18", fg=MUTED,
            font=("Segoe UI", 9), anchor="center",
        )
        self.enemy_level_label.grid(row=1, column=0, sticky="ew", pady=(0, 7))
        self.enemy_health = tk.Frame(self.enemy_group, bg="#131a18", height=20)
        self.enemy_health.grid(row=2, column=0, sticky="ew", pady=(0, 12))
        self.enemy_health.grid_propagate(False)
        self.enemy_hp_bar = ttk.Progressbar(
            self.enemy_health, style="EnemyHealth.Horizontal.TProgressbar", length=175,
        )
        self.enemy_hp_bar.place(relx=0.5, rely=0.5, anchor="center")
        self.enemy_hp_label = tk.Label(
            self.enemy_health, text="", bg="#131a18", fg=INK,
            font=("Consolas", 9), anchor="e",
        )
        self.enemy_hp_label.place(
            relx=0.5, rely=0.5, x=97, anchor="w",
        )
        self.enemy_image_label = tk.Label(
            self.enemy_group, text="", bg="#131a18", borderwidth=0,
            anchor="center",
        )
        self.enemy_image_label.grid(row=3, column=0)
        self.enemy_images = {}
        self.current_enemy_image_id = None

        self.log_frame = tk.Frame(center, bg=PANEL, highlightthickness=1, highlightbackground=EDGE)
        self.log_frame.columnconfigure(0, weight=1)
        self._label(self.log_frame, "БОЕВОЙ ЛОГ", GOLD).grid(row=0, column=0, sticky="w", padx=12, pady=(8, 4))
        self.battle_log = tk.Text(self.log_frame, height=5, wrap="word", bg="#131a18", fg=INK,
                                  font=("Segoe UI", 10), state="disabled", padx=12, pady=6, borderwidth=0)
        self.battle_log.grid(row=1, column=0, sticky="ew")
        log_scroll = ttk.Scrollbar(self.log_frame, command=self.battle_log.yview)
        log_scroll.grid(row=1, column=1, sticky="ns")
        self.battle_log.configure(yscrollcommand=log_scroll.set)
        for tag, color in COMBAT_LOG_COLORS.items():
            self.battle_log.tag_configure(tag, foreground=color)

        self.character_panel = CharacterPanel(stage)
        self.ability_panel = AbilityPanel(center, on_use=self.use_flask)
        self.ability_panel.grid(row=3, column=0, sticky="ew", pady=(6, 0))
        action_panel = StonePanel(center, height=180)
        self.action_panel = action_panel
        action_panel.grid(row=4, column=0, sticky="ew", pady=(10, 0))
        self.prompt_label = self._label(action_panel.content, "Игра загружается…", GOLD)
        self.prompt_label.pack(fill="x", pady=(2, 6))
        scroll_area = tk.Frame(action_panel.content, bg=PANEL)
        scroll_area.pack(fill="both", expand=True)
        self.action_canvas = tk.Canvas(scroll_area, bg=PANEL, highlightthickness=0, height=195)
        action_scroll = ttk.Scrollbar(scroll_area, command=self.action_canvas.yview)
        action_scroll.pack(side="right", fill="y")
        self.action_canvas.pack(side="left", fill="both", expand=True)
        self.action_canvas.configure(yscrollcommand=action_scroll.set)
        self.buttons = tk.Frame(self.action_canvas, bg=PANEL)
        for column in range(2):
            self.buttons.columnconfigure(column, weight=1, uniform="actions")
        window = self.action_canvas.create_window(0, 0, window=self.buttons, anchor="nw")
        self.buttons.bind("<Configure>", lambda e: self.action_canvas.configure(scrollregion=self.action_canvas.bbox("all")))
        self.action_canvas.bind("<Configure>", lambda e: self.action_canvas.itemconfigure(window, width=e.width))
        root.bind("<MouseWheel>", self._scroll_actions, add="+")

        entry_row = tk.Frame(center, bg=BG)
        self.entry_row = entry_row
        entry_row.grid(row=5, column=0, sticky="ew", pady=(6, 0))
        entry_row.grid_remove()
        self._label(entry_row, "Ввод", MUTED, bg=BG).pack(side="left", padx=(0, 8))
        self.value = tk.StringVar()
        self.entry = ttk.Entry(entry_row, textvariable=self.value, state="disabled")
        self.entry.pack(side="left", fill="x", expand=True)
        self.entry.bind("<Return>", lambda e: self.submit(self.value.get()))
        self.send = self._button(entry_row, "Отправить / Enter", lambda: self.submit(self.value.get()))
        self.send.configure(state="disabled")
        self.send.pack(side="left", padx=(8, 0))
        self.status = self._label(center, "", MUTED, bg=BG, font=("Segoe UI", 9))
        self.status.grid(row=6, column=0, sticky="ew", pady=(6, 0))

        self.right = StonePanel(outer, width=225)
        self.right.grid(row=1, column=2, sticky="nsew", padx=(10, 0))
        card = self.right.content
        self._label(card, "ПЕРСОНАЖ", GOLD).pack(anchor="w", pady=(10, 16))
        self.name_label = self._label(card, "Герой ещё не создан", INK, font=("Georgia", 16))
        self.name_label.pack(fill="x")
        self.class_label = self._label(card, "Выберите имя и класс", MUTED)
        self.class_label.pack(fill="x", pady=(4, 18))
        self.hp_label = self._label(card, "HP  —", INK)
        self.hp_label.unbind("<Configure>")
        self.hp_label.configure(wraplength=0)
        self.hp_label.pack(anchor="w")
        self.hp_bar = ttk.Progressbar(card, style="Health.Horizontal.TProgressbar")
        self.hp_bar.pack(fill="x", pady=(5, 12))
        self.mp_label = self._label(card, "MP  —", INK)
        self.mp_label.pack(anchor="w")
        self.mp_bar = ttk.Progressbar(card, style="Mana.Horizontal.TProgressbar")
        self.mp_bar.pack(fill="x", pady=(5, 20))
        self.details_label = self._label(card, "", INK, font=("Segoe UI", 11))
        self.details_label.pack(fill="x")
        self.gear_label = self._label(card, "", MUTED, font=("Segoe UI", 10))
        self.gear_label.pack(fill="x", pady=(20, 0))
        self.gear_tooltip_rows = ()
        self.gear_tooltip = DelayedTooltip(self.right)
        self.gear_tooltip.bind_to(self.gear_label, lambda: self.gear_tooltip_rows)
        self.poll_id = root.after(25, self.poll)
        if game is not None:
            self.start(game)

    def _style(self):
        style = ttk.Style(self.root)
        style.theme_use("clam")
        style.configure(".", background=PANEL, foreground=INK, fieldbackground=BG,
                        troughcolor=BG, bordercolor=EDGE, lightcolor=PANEL, darkcolor=PANEL)
        style.configure("TEntry", padding=6, insertcolor=INK)
        style.map("TEntry", fieldbackground=[("disabled", PANEL)], foreground=[("disabled", MUTED)])
        style.configure("TSpinbox", padding=6, arrowsize=18, arrowcolor=GOLD)
        style.configure("TCheckbutton", padding=5)
        style.map("TCheckbutton", background=[("active", "#30382f")], foreground=[("disabled", "#757b70")])
        style.configure("TScrollbar", background="#333b33", arrowcolor=GOLD, gripcount=0)
        style.map("TScrollbar", background=[("active", "#515a46")])
        style.configure("Health.Horizontal.TProgressbar", background="#a04842", troughcolor="#302221", borderwidth=0)
        style.configure("EnemyHealth.Horizontal.TProgressbar", background="#c84c48", troughcolor="#351f20", borderwidth=0, thickness=7)
        style.configure("Mana.Horizontal.TProgressbar", background="#527aa0", troughcolor="#202d37", borderwidth=0)

    def _label(self, master, text, color=INK, font=("Segoe UI", 10), bg=PANEL):
        label = tk.Label(master, text=text, bg=bg, fg=color, anchor="w", justify="left", font=font)
        label.bind("<Configure>", lambda e: label.configure(wraplength=max(80, e.width - 4)))
        return label

    def _button(self, master, text, command):
        button = tk.Button(master, text=text, command=command, bg="#2b322a", fg=INK,
                           activebackground="#424936", activeforeground="#f1e5bf",
                           disabledforeground="#767c70", highlightthickness=1,
                           highlightbackground=EDGE, highlightcolor=GOLD, relief="flat",
                           borderwidth=0, font=("Segoe UI", 10), anchor="w", justify="left", padx=10, pady=8)
        button.bind("<Configure>", lambda e: button.configure(wraplength=max(70, e.width - 24)))
        return button

    def _add_action(self, text, command, position=None):
        index = len(self.buttons.winfo_children()) if position is None else position
        button = self._button(self.buttons, text, command)
        button.grid(row=index // 2, column=index % 2, sticky="nsew", padx=3, pady=3)
        return button

    def _clear_actions(self):
        for row in range(self.buttons.grid_size()[1]):
            self.buttons.rowconfigure(row, minsize=0)
        for child in self.buttons.winfo_children():
            child.destroy()
        self.action_canvas.yview_moveto(0)

    def _scroll_actions(self, event):
        widget = event.widget
        while widget is not None:
            if widget == self.action_canvas:
                self.action_canvas.yview_scroll(-int(event.delta / 120), "units")
                return "break"
            widget = getattr(widget, "master", None)

    def start(self, game):
        backend = self.io
        def run():
            try:
                with use_backend(backend):
                    game()
            except GameClosed:
                pass
            except Exception:
                backend.events.put(("text", "\nОшибка игры:\n" + traceback.format_exc()))
                backend.events.put(("done", "Игра остановлена из-за ошибки. Подробности на экране."))
            else:
                backend.events.put(("done", "Игра завершена. Окно можно закрыть."))
        self.worker = threading.Thread(target=run, name="axe-and-sword-game", daemon=True)
        self.worker.start()

    def append(self, text):
        text = self.ansi_tail + text
        self.ansi_tail = ""
        tail = text.rfind("\x1b")
        if tail >= 0 and re.fullmatch(r"\x1b(?:\[[0-9;]*)?", text[tail:]):
            self.ansi_tail, text = text[tail:], text[:tail]
        self.text.configure(state="normal")
        offset = 0
        for match in ANSI.finditer(text):
            self.text.insert("end", text[offset:match.start()], self.foreground)
            for code in (match.group(1) or "0").split(";"):
                if code in ("0", "39"):
                    self.foreground = "37"
                elif code in COLORS:
                    self.foreground = code
            offset = match.end()
        self.text.insert("end", text[offset:], self.foreground)
        self.text.configure(state="disabled")

    def render(self, screen):
        self.character_panel.hide()
        self.title.configure(text=screen["title"])
        self.text.configure(state="normal")
        self.text.delete("1.0", "end")
        self.text.configure(state="disabled")
        self.foreground, self.ansi_tail = "37", ""
        body = screen.get("body", "")
        if screen["kind"] == "battle":
            self.battle_stage.configure(pady=0)
            self.battle_log.configure(height=3)
            self.action_canvas.configure(height=90)
            self.text.grid_remove()
            self.stage_vertical.grid_remove()
            self.stage_horizontal.grid_remove()
            self.battle_stage.grid(row=0, column=0, sticky="nsew")
            self._render_enemy(screen)
        else:
            self.action_canvas.configure(height=195)
            self.battle_stage.grid_remove()
            self.text.grid()
            self.stage_vertical.grid()
            self.stage_horizontal.grid()
        if screen["kind"] in ("location", "overlay"):
            # Wrap prose but retain ASCII panels and item layouts in other views.
            width = max(35, (max(self.text.winfo_width(), 440) - 45) // 9)
            body = "\n".join(textwrap.fill(line, width=width) for line in body.splitlines())
        if screen["kind"] != "battle":
            self.append(body)
        self.text.yview_moveto(0)
        if screen["kind"] == "battle":
            self.log_frame.grid(row=2, column=0, sticky="ew", pady=(10, 0))
            self.battle_log.configure(state="normal")
            self.battle_log.delete("1.0", "end")
            self._render_battle_log(screen.get("messages", ()))
            self.battle_log.configure(state="disabled")
            self.battle_log.see("end")
        else:
            self.log_frame.grid_remove()

    def _render_enemy(self, screen):
        self.enemy_name_label.configure(text=screen["enemy_name"])
        self.enemy_level_label.configure(text=f"Уровень {screen['enemy_level']}")
        maximum = max(1, screen["enemy_max_health"])
        self.enemy_hp_bar.configure(
            maximum=maximum,
            value=max(0, screen["enemy_health"]),
        )
        self.enemy_hp_label.configure(
            text=f"{screen['enemy_health']} / {screen['enemy_max_health']}"
        )
        image_id = screen.get("enemy_image_id")
        self.current_enemy_image_id = image_id
        image = self._enemy_image(image_id)
        self.enemy_image_label.configure(image=image, text="")

    def _enemy_image(self, image_id):
        path = ENEMY_IMAGE_FILES.get(image_id)
        if path is None or not path.is_file():
            return ""
        if image_id not in self.enemy_images:
            try:
                source = tk.PhotoImage(master=self.root, file=str(path))
            except (tk.TclError, OSError):
                return ""
            background = source.get(0, 0)
            points = []
            for y in range(source.height()):
                for x in range(source.width()):
                    if source.get(x, y) == background:
                        source.transparency_set(x, y, True)
                    elif not source.transparency_get(x, y):
                        points.append((x, y))
            if not points:
                return ""
            left, top = min(x for x,y in points), min(y for x,y in points)
            right, bottom = max(x for x,y in points)+1, max(y for x,y in points)+1
            cropped = tk.PhotoImage(master=self.root, width=right-left, height=bottom-top)
            cropped.tk.call(str(cropped), "copy", str(source), "-from", left, top, right, bottom, "-to", 0, 0)
            self.enemy_images[image_id] = cropped.zoom(ENEMY_ART.get(image_id, {}).get("scale", 2))
        return self.enemy_images[image_id]

    def _render_battle_log(self, messages):
        messages = tuple(messages)
        for index, message in enumerate(messages):
            critical_damage = (
                index + 1 < len(messages)
                and "крит" in messages[index + 1].lower()
            )
            for text, tag in combat_message_segments(message, critical_damage):
                self.battle_log.insert("end", text, tag or ())
            if index + 1 < len(messages):
                self.battle_log.insert("end", "\n")

    def update_character(self, data):
        self.character = data
        self.name_label.configure(text=data["name"])
        self.class_label.configure(text=f"{data['class']}  ·  Уровень {data['level']}")
        self.hp_label.configure(text=f"HP   {data['health']} / {data['max_health']}")
        self.mp_label.configure(text=f"MP   {data['mana']} / {data['max_mana']}")
        self.hp_bar.configure(maximum=max(1, data["max_health"]), value=max(0, data["health"]))
        self.mp_bar.configure(maximum=max(1, data["max_mana"]), value=max(0, data["mana"]))
        self.ability_panel.refresh(data["flasks"])
        self.details_label.configure(text=f"Броня     {data['armor']}\nУрон       {data['damage']}\n\nОпыт       {data['exp']} / {data['exp_to_level']}\nЗолото    {data['gold']}\nРюкзак    {data['inventory']}")
        self.gear_label.configure(text="В руках\n" + ANSI.sub("", data["equipment"][0][1]))
        main_hand = next((entry for entry in data["equipment_slots"]
                          if entry["id"] == "main_hand"), None)
        self.gear_tooltip_rows = main_hand["tooltip"] if main_hand and main_hand["name"] != "—" else ()

    def use_flask(self, resource):
        if self.ability_panel.enabled.get(resource):
            self.submit("flask:" + resource)

    def _update_globals(self):
        flask_allowed = bool(self.waiting and not self.overlay and self.prompt and (
            self.prompt.kind == "location" or
            (self.prompt.kind == "battle" and "3" in dict(self.prompt.choices))))
        self.ability_panel.set_context(flask_allowed)
        for action, button in self.global_buttons.items():
            readonly = action in ("character", "map")
            allowed = self.waiting and self.character is not None and (
                (readonly and (action != "map" or bool(self.map_data))) or
                (self.prompt.kind == "location" and action in self.routes))
            button.configure(state="normal" if allowed else "disabled")
            button.configure(text=self.global_labels[action])

    def global_action(self, action):
        if not self.waiting or self.character is None:
            return
        if action == "inventory":
            if self.prompt.kind == "location" and action in self.routes:
                self.open_inventory()
            return
        if action in ("loot_filter", "exit"):
            if self.prompt.kind == "location" and action in self.routes:
                self.overlay = None
                self.submit(self.routes[action])
            return
        data = self.character
        if action == "character":
            title = "Персонаж"
            body = f"{data['name']} · {data['class']}\n\nУровень: {data['level']}\nHP: {data['health']} / {data['max_health']}\nMP: {data['mana']} / {data['max_mana']}\n\nSTR / Сила: {data['strength']}\nDEX / Ловкость: {data['dexterity']}\nINT / Интеллект: {data['intelligence']}\n\nБроня: {data['armor']}\nУрон: {data['damage']}\nЗолото: {data['gold']}\nОпыт: {data['exp']} / {data['exp_to_level']}\nНераспределённые очки: {data['unspent']}"
        elif action == "map":
            title = "Карта мира"
            body = "\n\n".join(f"{'[Вы здесь] ' if here else ''}{name}\n  Пути: {', '.join(paths)}" +
                                (f"\n  {blocked}" if blocked else "") for here, name, paths, blocked in self.map_data)
        else:
            return
        self.overlay = action
        self.render({"kind": "overlay", "title": title, "body": body})
        if action == "character":
            self.text.grid_remove()
            self.stage_vertical.grid_remove()
            self.stage_horizontal.grid_remove()
            self.character_panel.refresh(data)
            self.character_panel.grid(row=0, column=0, sticky="nsew")
        self.entry_row.grid_remove()
        self._clear_actions()
        self.prompt_label.configure(text="Просмотр · игровой ход не расходуется")
        self._add_action("Вернуться к игре", self.close_overlay)
        if self.prompt.kind == "location":
            if action == "character":
                self._add_action("Изменить экипировку", lambda: self.global_action("inventory"))
            elif action == "map":
                self._add_action("Переместиться", lambda: self._overlay_route("move"))
        self.entry.configure(state="disabled")
        self.send.configure(state="disabled")
        self._update_globals()

    def _overlay_route(self, action):
        if self.prompt.kind == "location" and action in self.routes:
            self.overlay = None
            self.submit(self.routes[action])

    def close_overlay(self):
        value = self.value.get()
        self.overlay = None
        self.render(self.last_screen)
        self.show_prompt(replace(self.prompt, default=value), redraw=False)

    def open_inventory(self):
        player = self.io.player
        if player is None:
            return
        if self.inventory_window is not None and self.inventory_window.winfo_exists():
            self.inventory_window.refresh()
            self.inventory_window.lift()
            return
        self.inventory_window = InventoryWindow(
            self.root,
            player,
            on_change=self._inventory_changed,
            on_close=self._inventory_closed,
            anchor=self.stage,
            position=self.inventory_position,
            on_position=lambda position: setattr(self, "inventory_position", position),
        )

    def _inventory_changed(self):
        if self.io.player is not None:
            data = character_snapshot(self.io.player)
            self.update_character(data)
            if self.overlay == "character":
                self.character_panel.refresh(data)

    def _inventory_closed(self):
        self.inventory_window = None

    def show_prompt(self, prompt, redraw=True):
        self.prompt = prompt
        self.waiting = True
        self.overlay = None
        self._clear_actions()
        if redraw and prompt.body.strip():
            if prompt.kind == "pause" and self.last_screen["kind"] == "battle":
                self.last_screen = dict(self.last_screen, messages=(
                    *self.last_screen.get("messages", ()), prompt.body.strip()))
            else:
                self.last_screen = {"kind": "menu", "title": prompt.text.strip().rstrip(": "),
                                    "body": prompt.body.strip()}
            self.render(self.last_screen)
        self.prompt_label.configure(text=prompt.text.strip())
        self.value.set(prompt.default)
        self.entry.configure(state="normal")
        self.send.configure(state="normal")
        self.status.configure(text="Выберите действие кнопкой")
        if prompt.kind == "text":
            self.entry_row.grid()
        else:
            self.entry_row.grid_remove()
        if prompt.kind == "multiple":
            selected = []
            for index, (key, label) in enumerate(prompt.choices):
                variable = tk.BooleanVar(value=key in self.value.get().split(","))
                selected.append((key, variable))
                ttk.Checkbutton(self.buttons, text=label, variable=variable,
                                command=lambda: self.value.set(",".join(k for k, v in selected if v.get()))).grid(
                                    row=index // 2, column=index % 2, sticky="ew", padx=3, pady=3)
            self._add_action("Применить выбранное", lambda: self.submit(self.value.get()))
            self._add_action("Показывать все", lambda: self.submit(""))
        elif prompt.kind == "number":
            self.value.set(prompt.default or "1")
            ttk.Spinbox(self.buttons, from_=1, to=999999, textvariable=self.value, width=10).grid(row=0, column=0, sticky="ew", padx=3, pady=3)
            self._add_action("Применить", lambda: self.submit(self.value.get()))
        elif prompt.kind == "pause":
            self._add_action("Продолжить", lambda: self.submit(""))
        elif prompt.kind == "text":
            self._add_action("Начать игру", lambda: self.submit(self.value.get()))
        else:
            global_keys = {self.routes.get(action) for action in ("inventory", "loot_filter", "exit")} if prompt.kind == "location" else set()
            if prompt.kind == "battle":
                available = dict(prompt.choices)
                for key, label, position in (("1", "Атака", 0), ("3", "Использовать зелье", 1), ("2", "Завершить ход", 2)):
                    button = self._add_action(label, lambda value=key: self.submit(value), position)
                    if key not in available:
                        button.configure(state="disabled")
            else:
                for key, label in prompt.choices:
                    if key in global_keys:
                        continue
                    position = int(key) - 1 if key.isdigit() and int(key) > 0 else len(prompt.choices)
                    if prompt.kind == "location":
                        action = next((a for a, k in self.routes.items() if k == key), key)
                        if action not in self.location_slots:
                            self.location_slots[action] = len(self.location_slots)
                        position = self.location_slots[action]
                    button = self._add_action(label, lambda value=key: self.submit(value), position)
                    if prompt.kind == "location":
                        button.configure(height=2)
                        for row in range(position // 2 + 1):
                            self.buttons.rowconfigure(row, minsize=button.winfo_reqheight() + 6)
        self._update_globals()
        self.entry.focus_set()

    def submit(self, value):
        if not self.waiting or self.io.closed.is_set() or self.overlay:
            return
        if (self.prompt.kind == "location"
                and value == self.routes.get("inventory")):
            self.open_inventory()
            return
        if self.inventory_window is not None:
            self.inventory_window.close()
        self.waiting = False
        self.entry.configure(state="disabled")
        self.send.configure(state="disabled")
        for child in self.buttons.winfo_children():
            child.configure(state="disabled")
        self._update_globals()
        self.status.configure(text="Выполняется действие…")
        self.io.answers.put(value)

    def poll(self):
        for _ in range(300):
            try:
                event, payload = self.io.events.get_nowait()
            except queue.Empty:
                break
            if event == "text":
                self.output += payload
            elif event == "clear":
                self.output = ""
            elif event == "character":
                self.update_character(payload)
            elif event == "map":
                self.map_data = payload
            elif event == "notice":
                self.notice = payload
                self.output = ""
            elif event == "screen":
                self.last_screen = payload
                if payload["kind"] == "location":
                    self.routes = payload["routes"]
                    if self.notice:
                        self.last_screen = dict(payload, body=payload["body"] + "\n\n" + self.notice)
                        self.notice = ""
                self.render(self.last_screen)
                self.output = ""
            elif event == "prompt":
                self.show_prompt(payload)
                self.output = ""
            elif event == "done":
                self.waiting = False
                if self.output.strip():
                    self.last_screen = {"kind": "menu", "title": "Axe and Sword", "body": self.output.strip()}
                    self.render(self.last_screen)
                self.entry.configure(state="disabled")
                self.send.configure(state="disabled")
                self._clear_actions()
                self._update_globals()
                self.status.configure(text=payload)
                self.prompt_label.configure(text=payload)
                self._add_action("Закрыть окно", self.close)
        self.poll_id = self.root.after(25, self.poll)

    def close(self):
        self.ability_panel.tooltip.hide()
        self.character_panel.tooltip.hide()
        if self.inventory_window is not None and self.inventory_window.winfo_exists():
            self.inventory_window.close()
        self.io.close()
        self.root.after_cancel(self.poll_id)
        self.root.destroy()


def launch():
    from main import start_game
    root = tk.Tk()
    GameWindow(root, start_game)
    root.mainloop()


if __name__ == "__main__":
    launch()


