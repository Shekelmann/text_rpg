import io
import gc
import random
import threading
import time
import tkinter as tk
import unittest
from unittest.mock import patch

import game_io
from gui import (
    DesktopIO,
    GameClosed,
    GameWindow,
    Prompt,
    combat_message_segments,
    menu_choices,
)


class TestDesktopBridge(unittest.TestCase):
    def test_combat_log_segments_color_only_requested_information(self):
        cases = (
            ("Яд наносит Гоблину 2 урона.", "poison", "Яд2урона"),
            ("Кровотечение наносит вам 3 урона.", "bleeding", "Кровотечение3урона"),
            ("Иссушение наносит врагу 4 урона и восстанавливает 2 HP, 2 MP.", "drain", "Иссушение4урона"),
            ("Вы наносите врагу 12 урона.", "critical", "12урона"),
            ("Критический удар!", "critical", "Критическийудар"),
            ("Вы проиграли бой.", "defeat", "Вы проиграли бой."),
        )
        for message, expected_tag, expected_text in cases:
            with self.subTest(message=message):
                segments = combat_message_segments(
                    message,
                    critical_damage=message.startswith("Вы наносите"),
                )
                colored = "".join(text for text, tag in segments if tag == expected_tag)
                self.assertEqual(colored, expected_text)

    def test_boxed_and_colored_menus_preserve_numbers(self):
        self.assertEqual(menu_choices(
            "║ 2 - Завершить ход  ║\n║ 12. \033[35mМеч\033[0m ║\n0. Назад"),
            (("2", "Завершить ход"), ("12", "Меч"), ("0", "Назад")))

    def test_redraw_replaces_previous_choices(self):
        self.assertEqual(menu_choices("1. Старое\n2. Старое\n1. Новое\n0. Назад"),
                         (("1", "Новое"), ("0", "Назад")))

    def test_console_still_uses_builtin_input_and_output(self):
        with patch("builtins.input", return_value="2") as read:
            self.assertEqual(game_io.input("Выбор", kind="number", default="1"), "2")
            read.assert_called_once_with("Выбор")
        output = io.StringIO()
        game_io.print("a", "b", sep="|", end="!", file=output)
        self.assertEqual(output.getvalue(), "a|b!")

    def test_backend_is_thread_local_and_restored(self):
        backend = DesktopIO()
        with patch("builtins.print") as output:
            with game_io.use_backend(backend):
                game_io.print("window")
                thread = threading.Thread(target=lambda: game_io.print("terminal"))
                thread.start()
                thread.join(1)
            game_io.print("restored")
        self.assertEqual(backend.events.get_nowait(), ("text", "window\n"))
        self.assertEqual(output.call_count, 2)

    def test_prompt_boundaries_and_confirmation(self):
        backend = DesktopIO()
        backend.write("1. Меч\n2. Зелье\n")
        backend.answers.put("2")
        self.assertEqual(backend.read("Предмет"), "2")
        backend.answers.put("0")
        backend.read("Купить?", choices=(("1", "Да"), ("0", "Нет")))
        backend.answers.put("")
        backend.read("Продолжить", kind="pause")
        prompts = []
        while not backend.events.empty():
            event, payload = backend.events.get_nowait()
            if event == "prompt":
                prompts.append(payload)
        self.assertEqual(prompts[0].choices, (("1", "Меч"), ("2", "Зелье")))
        self.assertEqual(prompts[1].choices, (("1", "Да"), ("0", "Нет")))
        self.assertEqual(prompts[2].choices, ())

    def test_close_unblocks_input(self):
        backend = DesktopIO()
        stopped = threading.Event()

        def read():
            try:
                backend.read("Введите имя", kind="text")
            except GameClosed:
                stopped.set()

        thread = threading.Thread(target=read, daemon=True)
        thread.start()
        backend.events.get(timeout=1)
        backend.close()
        thread.join(1)
        self.assertTrue(stopped.is_set())

    def test_return_pause_does_not_wait_but_console_keeps_enter(self):
        backend = DesktopIO()
        backend.write("Вы сняли оружие.\n")
        self.assertEqual(backend.read("Enter", kind="return"), "")
        events = []
        while not backend.events.empty():
            events.append(backend.events.get_nowait())
        self.assertIn(("notice", "Вы сняли оружие."), events)
        self.assertFalse(any(event == "prompt" for event, _ in events))
        with patch("builtins.input", return_value="") as read:
            game_io.input("Enter", kind="return")
            read.assert_called_once_with("Enter")


class TestGameWindow(unittest.TestCase):
    """Exercise actual Tk controls and unchanged game functions together."""

    def setUp(self):
        # Dispose prior Tcl interpreters on their owning thread, before workers.
        gc.collect()
        try:
            self.root = tk.Tk()
        except tk.TclError as error:
            self.skipTest(f"Tk display unavailable: {error}")
        self.root.withdraw()
        self.app = GameWindow(self.root)

    def tearDown(self):
        self.app.close()
        if self.app.worker:
            self.app.worker.join(2)
            self.assertFalse(self.app.worker.is_alive())
        self.app = None
        self.root = None
        gc.collect()

    def wait_for(self, predicate):
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            self.root.update()
            if predicate():
                return
            time.sleep(0.005)
        self.fail("GUI timed out:\n" + self.app.text.get("1.0", "end")[-2000:])

    def click(self, label):
        self.wait_for(lambda: self.app.waiting)
        candidates = [*self.app.buttons.winfo_children(), *self.app.global_buttons.values()]
        matches = [button for button in candidates
                   if label in str(button.cget("text")) and str(button.cget("state")) != "disabled"]
        self.assertEqual(len(matches), 1, (label, self.app.prompt))
        matches[0].invoke()

    def done(self):
        self.wait_for(lambda: "Игра завершена" in self.app.status.cget("text"))
        self.assertNotIn("Traceback", self.app.text.get("1.0", "end"))

    def test_full_game_creation_inventory_movement_trade_and_exit(self):
        from main import start_game
        self.app.start(start_game)
        self.click("Начать игру")
        self.click("1.")
        self.click("Описание локации")
        self.wait_for(lambda: self.app.waiting)
        self.assertIn("Обычная маленькая деревня", self.app.text.get("1.0", "end"))
        self.click("Открыть инвентарь")
        self.wait_for(lambda: self.app.inventory_window is not None)
        inventory_window = self.app.inventory_window
        weapon_slot = next(
            index for index, item in enumerate(inventory_window.inventory.slots)
            if getattr(item, "is_weapon", False)
        )
        self.assertTrue(inventory_window.equip_slot(weapon_slot))
        self.assertTrue(inventory_window.winfo_exists())
        inventory_window.close()
        self.click("Переместиться")
        self.click("таверну")
        self.click("Поговорить")
        self.click("1. Купить")
        self.click("1.")
        self.click("0. Нет")
        self.click("0. Назад")
        self.click("2. Продать")
        self.click("1.")
        self.click("1. Да")
        self.click("0. Назад")
        self.click("1. Купить")
        self.click("1.")
        self.click("1. Да")
        self.click("0. Назад")
        self.click("0. Назад")
        self.click("Выйти из игры")
        self.done()
        journal = self.app.text.get("1.0", "end")
        self.assertNotIn("Обычная маленькая деревня", journal)
        self.assertNotIn("\033[", journal)

    def test_persistent_card_readonly_views_and_map_navigation(self):
        from main import start_game
        self.app.start(start_game)
        self.click("Начать игру")
        self.click("1.")
        self.wait_for(lambda: self.app.waiting)
        self.assertEqual(self.app.name_label.cget("text"), "Герой")
        original = dict(self.app.character)
        self.click("Персонаж")
        self.assertIn("STR / Сила", self.app.character_panel.stats.cget("text"))
        self.assertTrue(self.app.io.answers.empty())
        self.assertNotIn("equipment", self.app.global_buttons)
        self.assertIn("main_hand", self.app.character_panel.slot_widgets)
        self.click("Вернуться к игре")
        self.assertEqual(original, self.app.character)
        self.click("Карта")
        self.assertIn("[Вы здесь]", self.app.text.get("1.0", "end"))
        self.click("Переместиться")
        self.click("таверну")
        self.wait_for(lambda: self.app.waiting)
        self.assertIn("Три пенька", self.app.title.cget("text"))
        self.assertNotIn("Обычная маленькая деревня", self.app.text.get("1.0", "end"))
        self.click("Выйти из игры")
        self.done()

    def test_battle_redraw_has_one_log_and_fresh_character_stats(self):
        from interface import show_battle_screen
        from player import Player
        from encounter import create_enemy
        player = Player("Hero", None)
        enemy = create_enemy("wolf", 1)
        with game_io.use_backend(self.app.io):
            show_battle_screen(player, enemy, ["Первое событие"])
            player.health -= 2
            show_battle_screen(player, enemy, ["Первое событие", "Второе событие"])
            show_battle_screen(player, enemy, ["Первое событие", "Второе событие"])
        self.wait_for(lambda: self.app.character is not None)
        log = self.app.battle_log.get("1.0", "end")
        self.assertEqual(log.count("Первое событие"), 1)
        self.assertEqual(log.count("Второе событие"), 1)
        self.assertNotIn("Первое событие", self.app.text.get("1.0", "end"))
        self.assertEqual(self.app.character["health"], player.health)
        self.app.show_prompt(Prompt("Действие", "menu", (("1", "Атака"),)))
        self.assertEqual(str(self.app.global_buttons["inventory"].cget("state")), "disabled")
        self.click("Персонаж")
        self.click("Вернуться к игре")
        self.assertEqual(self.app.battle_log.get("1.0", "end"), log)

    def test_enemy_stage_shows_level_health_and_optional_goblin_image(self):
        from encounter import create_enemy
        from interface import show_battle_screen
        from player import Player

        player = Player("Hero", None)
        goblin = create_enemy("goblin", 3)
        goblin.health = 25
        goblin.max_health = 100
        with game_io.use_backend(self.app.io):
            show_battle_screen(player, goblin, ["Начало боя"])
        self.wait_for(lambda: self.app.last_screen["kind"] == "battle")

        self.assertEqual(self.app.enemy_name_label.cget("text"), "Гоблин")
        self.assertEqual(self.app.enemy_level_label.cget("text"), "Уровень 3")
        self.assertEqual(self.app.enemy_hp_label.cget("text"), "25 / 100")
        self.assertEqual(float(self.app.enemy_hp_bar.cget("value")), 25)
        self.assertTrue(self.app.enemy_image_label.cget("image"))
        self.assertEqual(
            self.app.enemy_images["goblin"].width(),
            self.app.enemy_images["goblin"].height(),
        )
        self.assertTrue(self.app.enemy_images["goblin"].transparency_get(0, 0))

        wolf = create_enemy("wolf", 2)
        with game_io.use_backend(self.app.io):
            show_battle_screen(player, wolf, ["Другой бой"])
        self.wait_for(lambda: self.app.last_screen.get("enemy_name") == "Волк")
        self.assertTrue(self.app.enemy_image_label.cget("image"))

        self.root.geometry("1040x700")
        self.root.deiconify()
        self.root.update()
        stage_center = (
            self.app.battle_stage.winfo_rootx()
            + self.app.battle_stage.winfo_width() / 2
        )
        bar_center = (
            self.app.enemy_hp_bar.winfo_rootx()
            + self.app.enemy_hp_bar.winfo_width() / 2
        )
        self.assertAlmostEqual(bar_center, stage_center, delta=2)
        self.assertGreater(
            self.app.enemy_hp_label.winfo_rootx(),
            self.app.enemy_hp_bar.winfo_rootx() + self.app.enemy_hp_bar.winfo_width(),
        )

    def test_new_enemy_art_in_main_and_optional_encounters(self):
        from encounter import handle_encounter, hunt_optional_enemies
        from interface import show_battle_screen
        from player import Player
        from world import World

        player = Player("Hero", None)
        self.root.geometry("1040x700")
        self.root.deiconify()
        for enemy_id in ("wolf", "leshy", "likho"):
            for optional in (False, True):
                with self.subTest(enemy=enemy_id, optional=optional):
                    world = World(random.Random(1))
                    seen = []

                    def display_battle(player, enemy, world, location):
                        seen.append(enemy.id)
                        show_battle_screen(player, enemy, ["Проверка арта"])
                        self.wait_for(lambda: self.app.last_screen.get("enemy_image_id") == enemy_id)
                        picture = self.app.enemy_images[enemy_id]
                        self.assertEqual((picture.width(), picture.height()), (256, 256))
                        self.root.update_idletasks()
                        label = self.app.enemy_image_label
                        displayed = str(label.cget("image"))
                        self.assertEqual(displayed, str(picture))
                        displayed_width = int(self.root.tk.call("image", "width", displayed))
                        displayed_height = int(self.root.tk.call("image", "height", displayed))
                        self.assertTrue(label.winfo_ismapped())
                        self.assertGreaterEqual(label.winfo_width(), displayed_width)
                        self.assertGreaterEqual(label.winfo_height(), displayed_height)
                        self.assertLessEqual(label.winfo_rooty() + label.winfo_height(),
                                             self.root.winfo_rooty() + self.root.winfo_height())
                        for point in ((0, 0), (255, 0), (0, 255), (255, 255)):
                            self.assertTrue(picture.transparency_get(*point))
                        return False

                    with game_io.use_backend(self.app.io), patch("encounter.battle", side_effect=display_battle):
                        if optional:
                            state = world.get_combat_state("forest")
                            state.update(main_encounter_completed=True, optional_enemies=[enemy_id],
                                         optional_enemy_levels=[1], optional_enemy_rarities=["common"])
                            with patch("encounter.choose_optional_enemy", return_value=0):
                                hunt_optional_enemies(player, "forest", world)
                        else:
                            with patch("encounter.random.choice", return_value=enemy_id):
                                handle_encounter(player, "forest", world)
                    self.assertEqual(seen, [enemy_id])

    def test_missing_and_invalid_art_clear_previous_picture(self):
        from pathlib import Path
        from tempfile import TemporaryDirectory
        from encounter import create_enemy
        from interface import show_battle_screen
        from player import Player

        with TemporaryDirectory() as directory:
            missing = Path(directory) / "missing.png"
            invalid = Path(directory) / "invalid.png"
            invalid.write_text("not an image", encoding="utf-8")
            for path in (missing, invalid):
                with self.subTest(path=path), game_io.use_backend(self.app.io):
                    show_battle_screen(Player("Hero", None), create_enemy("goblin", 1), [])
                    self.wait_for(lambda: self.app.last_screen.get("enemy_image_id") == "goblin")
                    self.assertTrue(self.app.enemy_image_label.cget("image"))
                    with patch.dict("gui.ENEMY_IMAGE_FILES", {"wolf": path}):
                        show_battle_screen(Player("Hero", None), create_enemy("wolf", 1), [])
                        self.wait_for(lambda: self.app.last_screen.get("enemy_image_id") == "wolf")
                        self.assertFalse(self.app.enemy_image_label.cget("image"))

    def test_player_card_keeps_hp_on_one_line_and_groups_details(self):
        from gui_views import character_snapshot
        from player import Player

        player = Player("Hero", None)
        player.health = player.max_health = 120
        self.app.update_character(character_snapshot(player))

        self.assertEqual(self.app.hp_label.cget("text"), "HP   120 / 120")
        self.assertEqual(int(self.app.hp_label.cget("wraplength")), 0)
        details = self.app.details_label.cget("text")
        self.assertEqual(
            details,
            "Броня     0\nУрон       —\n\n"
            "Опыт       0 / 100\nЗолото    1\nРюкзак    0 / 20",
        )
        self.assertNotIn("Очки", details)

    def test_battle_log_applies_effect_and_critical_tags(self):
        screen = {
            "kind": "battle",
            "title": "Бой",
            "body": "",
            "enemy_name": "Гоблин",
            "enemy_level": 1,
            "enemy_health": 20,
            "enemy_max_health": 20,
            "enemy_image_id": "goblin",
            "messages": (
                "Яд наносит Гоблину 2 урона.",
                "Кровотечение наносит Гоблину 3 урона.",
                "Вы наносите Гоблину 12 урона.",
                "Критический удар!",
                "Иссушение наносит Гоблину 4 урона и восстанавливает 2 HP, 2 MP.",
                "Вы проиграли бой.",
            ),
        }
        self.app.render(screen)

        def tagged_text(tag):
            ranges = self.app.battle_log.tag_ranges(tag)
            return "".join(
                self.app.battle_log.get(ranges[index], ranges[index + 1])
                for index in range(0, len(ranges), 2)
            )

        self.assertEqual(tagged_text("poison"), "Яд2урона")
        self.assertEqual(tagged_text("bleeding"), "Кровотечение3урона")
        self.assertEqual(tagged_text("critical"), "12уронаКритическийудар")
        self.assertEqual(tagged_text("drain"), "Иссушение4урона")
        self.assertEqual(tagged_text("defeat"), "Вы проиграли бой.")

    def test_inventory_return_skips_pause_and_refreshes_equipment(self):
        from main import start_game
        self.app.start(start_game)
        self.click("Начать игру")
        self.click("1.")
        self.click("Открыть инвентарь")
        self.wait_for(lambda: self.app.inventory_window is not None)
        inventory_window = self.app.inventory_window
        weapon_slot = next(
            index for index, item in enumerate(inventory_window.inventory.slots)
            if getattr(item, "is_weapon", False)
        )
        self.assertTrue(inventory_window.equip_slot(weapon_slot))
        equipped = self.app.character["equipment"][0][1]
        self.assertNotEqual(equipped, "—")
        self.assertTrue(inventory_window.winfo_exists())
        inventory_window.close()
        self.assertIsNone(self.app.inventory_window)
        self.click("Открыть инвентарь")
        self.wait_for(lambda: self.app.inventory_window is not None)
        self.assertEqual(self.app.prompt.kind, "location")
        self.assertEqual(self.app.character["equipment"][0][1], equipped)
        self.app.inventory_window.close()
        self.click("Выйти из игры")
        self.done()

    def test_inventory_window_grid_move_sort_tooltip_and_reopen(self):
        from gui_views import character_snapshot
        from objects import create_item
        from player import Player

        player = Player("Hero", None)
        sword = create_item("sword")
        axe = create_item("axe")
        player.inventory.add_item(sword, slot=2)
        player.inventory.add_item(axe, slot=8)
        self.app.io.player = player
        self.app.update_character(character_snapshot(player))
        self.app.prompt = Prompt("Действие", "location", ())
        self.app.routes = {"inventory": "3"}
        self.app.waiting = True

        self.app.open_inventory()
        window = self.app.inventory_window

        self.assertEqual(len(window.slot_widgets), 20)
        self.assertEqual(window.tooltip.delay_ms, 1000)
        self.assertTrue(window.move_item(2, 10))
        self.assertIs(player.inventory.item_at(10), sword)
        window.close()
        self.app.open_inventory()
        window = self.app.inventory_window
        self.assertIs(player.inventory.item_at(10), sword)
        window.sort_items()
        sword_slot = player.inventory.slot_of(sword)
        self.assertTrue(window.equip_slot(sword_slot))
        self.assertIs(player.main_hand, sword)
        self.assertTrue(window.winfo_exists())

        window.close()
        self.app.open_inventory()
        self.assertIsNot(self.app.inventory_window, window)
        self.assertIs(player.main_hand, sword)

    def test_filter_multiselect_and_numeric_mouse_controls(self):
        from interface import configure_loot_filter
        from player import Player
        from rarity import Rarity
        player = Player("Hero", None)
        self.app.start(lambda: configure_loot_filter(player))
        self.click("1. Редкость")
        self.click("2. Редкий")
        self.click("3. Эпический")
        self.click("Применить выбранное")
        self.click("4. Минимум")
        self.wait_for(lambda: self.app.waiting)
        spin = self.app.buttons.winfo_children()[0]
        self.root.deiconify()
        self.root.update()
        spin.event_generate("<ButtonPress-1>", x=spin.winfo_width() - 5, y=3)
        spin.event_generate("<ButtonRelease-1>", x=spin.winfo_width() - 5, y=3)
        self.click("Применить")
        self.click("0. Назад")
        self.done()
        self.assertEqual(player.loot_filter.rarities, {Rarity.RARE, Rarity.EPIC})
        self.assertEqual(player.loot_filter.minimum_affix_matches, 2)

    def test_combat_potion_level_up_chest_and_ground_loot(self):
        from battle import battle
        from damage import Damage_type
        from enemy import Enemy
        from interface import show_ground_loot
        from main import open_location_chest
        from objects import create_item
        from player import Player
        from world import World

        player = Player("Hero", create_item("sword"))
        player.health -= 5
        player.inventory.add_item(create_item("heal"))
        player.exp = player.exp_to_level - 1
        enemy = Enemy("Test enemy", 1, 0, 0, 0, Damage_type.PHYSICAL)
        world = World(random.Random(1))
        player.current_location = "forest"
        world.complete_main_encounter("forest")
        while world.get_optional_enemies("forest"):
            world.defeat_optional_enemy("forest", 0)
        dropped = create_item("dagger")
        world.add_ground_loot("forest", dropped)
        results = []

        def game():
            results.append(battle(player, enemy, world, "forest"))
            open_location_chest(player, world)
            show_ground_loot(player, world, "forest")

        with patch("battle.COMBAT_MESSAGE_DELAY", 0):
            self.app.start(game)
            self.click("3. Использовать зелье")
            self.click("1.")
            self.click("1. Атака")
            self.click("1. Сила")
            self.click("Продолжить")
            self.click("Продолжить")
            self.click("1.")
            self.click("0. Назад")
            self.done()
        self.assertEqual(results, [True])
        self.assertTrue(world.get_combat_state("forest")["chest_opened"])
        self.assertIn(dropped, player.inventory.items)
        self.assertEqual(world.get_ground_loot("forest"), ())
        self.assertEqual(player.unspent_stat_points, 0)

    def test_keyboard_double_click_guard_and_color_rendering(self):
        self.app.show_prompt(Prompt("Выбор", "menu", (("12", "Меч"),)))
        self.app.value.set("12")
        self.root.deiconify()
        self.root.update()
        self.app.entry.focus_force()
        self.root.update()
        self.app.entry.event_generate("<Return>")
        self.app.submit("12")
        self.assertEqual(self.app.io.answers.get_nowait(), "12")
        self.assertTrue(self.app.io.answers.empty())
        self.app.append("\033[3")
        self.app.append("5mМеч\033[0m")
        self.assertTrue(self.app.text.tag_ranges("35"))
        self.assertNotIn("\033", self.app.text.get("1.0", "end"))

    def test_game_exception_is_visible_without_console(self):
        def broken_game():
            raise ValueError("test failure")
        self.app.start(broken_game)
        self.wait_for(lambda: "ошибки" in self.app.status.cget("text"))
        self.assertIn("ValueError: test failure", self.app.text.get("1.0", "end"))

    def test_inventory_center_drag_reopen_refresh_and_clamp(self):
        from player import Player
        from types import SimpleNamespace
        self.app.io.player = Player("Hero", None)
        self.root.deiconify()
        self.root.update()
        self.app.open_inventory()
        window = self.app.inventory_window
        self.root.update()
        stage = self.app.stage
        self.assertAlmostEqual(window.winfo_x() + window.winfo_width() / 2,
                               stage.winfo_rootx() + stage.winfo_width() / 2, delta=2)
        self.assertAlmostEqual(window.winfo_y() + window.winfo_height() / 2,
                               stage.winfo_rooty() + stage.winfo_height() / 2, delta=2)
        x, y = window.winfo_x() + 15, window.winfo_y() + 15
        window._start_drag(SimpleNamespace(x_root=x, y_root=y))
        window._drag(SimpleNamespace(x_root=x + 35, y_root=y + 40))
        self.root.update()
        saved = self.app.inventory_position
        before = (window.winfo_x(), window.winfo_y())
        window.refresh()
        self.app.open_inventory()
        self.root.update()
        self.assertEqual(before, (window.winfo_x(), window.winfo_y()))
        window.close()
        self.app.open_inventory()
        self.root.update()
        self.assertEqual(saved, self.app.inventory_position)
        self.assertEqual(before, (self.app.inventory_window.winfo_x(), self.app.inventory_window.winfo_y()))
        self.app.inventory_window.close()
        self.app.inventory_position = (99999, -99999)
        self.app.open_inventory()
        self.root.update()
        window = self.app.inventory_window
        self.assertGreaterEqual(window.winfo_y(), self.root.winfo_rooty())
        self.assertLessEqual(window.winfo_x() + window.winfo_width(), self.root.winfo_rootx() + self.root.winfo_width())

    def test_sort_and_flask_tooltips_share_delay_and_hide(self):
        from player import Player
        from gui_views import character_snapshot
        player = Player("Hero", None)
        self.root.deiconify()
        self.root.update()
        self.app.io.player = player
        self.app.update_character(character_snapshot(player))
        self.app.open_inventory()
        window = self.app.inventory_window
        self.root.update()
        window.sort_button.event_generate("<Enter>")
        self.assertIsNotNone(window.tooltip.pending)
        self.assertIsNone(window.tooltip.window)
        self.assertEqual(window.tooltip.delay_ms, 1000)
        self.wait_for(lambda: window.tooltip.window is not None)
        tooltip_text = window.tooltip.window.winfo_children()[0].cget("text")
        self.assertIn("LEGENDARY → EPIC → RARE → COMMON", tooltip_text)
        window.sort_button.event_generate("<Leave>")
        self.assertIsNone(window.tooltip.window)
        panel = self.app.ability_panel
        self.assertEqual(panel.tooltip.delay_ms, window.tooltip.delay_ms)
        for key in ("hp", "mp"):
            lines = panel.flask_tooltip(key)
            self.assertIn(f"Восстанавливает {key.upper()}.", lines)
            self.assertIn("Количество восстановления пока не задано системой.", lines)
            panel.tooltip.enter(panel.flask_widgets[key][0], lines)
            panel.tooltip.leave()
            self.assertIsNone(panel.tooltip.pending)

    def test_character_accessories_existing_gear_and_noninvented_flasks(self):
        from player import Player, ARMOR_SLOTS
        from objects import create_item
        from gui_views import character_snapshot
        from types import SimpleNamespace
        player = Player("Hero", create_item("sword"))
        helmet = create_item("leather_helmet")
        player.inventory.add_item(helmet)
        player.equip_armor(helmet)
        before = player.inventory.slots
        self.app.update_character(character_snapshot(player))
        self.app.show_prompt(Prompt("Выберите", "location", ()))
        self.app.global_action("character")
        self.root.deiconify()
        self.root.update()
        panel = self.app.character_panel
        self.assertTrue(panel.winfo_ismapped())
        self.assertFalse(hasattr(self.app, "stats_label"))
        self.assertNotIn("equipment", self.app.global_buttons)
        for stat in ("STR", "DEX", "INT", "Свободные очки"):
            self.assertIn(stat, panel.stats.cget("text"))
        expected = {"main_hand", "off_hand", *ARMOR_SLOTS, "ring_1", "ring_2", "amulet", "belt"}
        self.assertEqual(set(panel.slot_widgets), expected)
        self.assertNotIn("feet", panel.slot_widgets)
        gear = {entry['id']: entry for entry in self.app.character['equipment_slots']}
        self.assertEqual(gear['head']['name'], helmet.name)
        self.assertTrue(gear['main_hand']['icon'])
        self.assertTrue(gear['ring_1']['future'])
        self.assertEqual(before, player.inventory.slots)
        self.assertTrue(all(entry['count'] is None for entry in self.app.character['flasks']))
        player.flasks = {'hp': SimpleNamespace(count=5, restore_amount=40),
                         'mp': SimpleNamespace(count=2, restore_amount=12)}
        self.app.update_character(character_snapshot(player))
        self.assertIn("Восстановление: 12 MP", self.app.ability_panel.flask_tooltip('mp'))
        player.flasks['mp'].count = 1
        self.app.update_character(character_snapshot(player))
        self.assertIn("Осталось: 1", self.app.ability_panel.flask_tooltip('mp'))

    def test_enemy_image_geometry_is_stable_across_hits(self):
        from interface import show_battle_screen
        from encounter import create_enemy
        from player import Player
        self.root.geometry("1040x880")
        self.root.deiconify()
        player, enemy = Player("Hero", None), create_enemy("wolf", 1)
        sizes = []
        for health in (enemy.health, enemy.health - 5, enemy.health - 10):
            enemy.health = health
            with game_io.use_backend(self.app.io):
                show_battle_screen(player, enemy, ["Попадание"])
            self.wait_for(lambda: self.app.last_screen.get('enemy_health') == health)
            self.root.update()
            widget = self.app.enemy_image_label
            sizes.append((widget.cget('image'), widget.winfo_width(), widget.winfo_height()))
            self.assertGreaterEqual(widget.winfo_width(), 256)
            self.assertGreaterEqual(widget.winfo_height(), 256)
            self.assertLessEqual(widget.winfo_rooty() + widget.winfo_height(),
                                 self.app.battle_stage.winfo_rooty() + self.app.battle_stage.winfo_height())
        self.assertEqual(sizes, [sizes[0]] * 3)

    def test_text_entry_only_for_text_and_skill_flask_slots_are_inert(self):
        self.root.deiconify()
        self.app.show_prompt(Prompt("Имя", "text", (), "Hero"))
        self.root.update()
        self.assertTrue(self.app.entry_row.winfo_ismapped())
        self.app.show_prompt(Prompt("Выбор", "menu", (("1", "Атака"),)))
        self.root.update()
        self.assertFalse(self.app.entry_row.winfo_ismapped())
        self.assertEqual(set(self.app.ability_panel.flask_widgets), {"hp", "mp"})
        self.assertEqual(len(self.app.ability_panel.skill_slots), 4)
        for widget in self.app.ability_panel.skill_slots:
            widget.invoke()
        self.assertTrue(self.app.io.answers.empty())
        self.click("1. Атака")
        self.assertEqual(self.app.io.answers.get_nowait(), "1")

    def test_loot_filter_help_matches_show_semantics(self):
        from interface import configure_loot_filter
        from player import Player
        self.app.start(lambda: configure_loot_filter(Player("Hero", None)))
        self.wait_for(lambda: self.app.waiting)
        self.assertIn("ПОКАЗЫВАЮТСЯ", self.app.text.get('1.0', 'end'))
        self.assertIn("Легендарные предметы всегда видны", self.app.text.get('1.0', 'end'))
        self.click("3. Аффиксы")
        self.wait_for(lambda: self.app.waiting)
        self.assertIn("ПОКАЗЫВАТЬ", self.app.text.get('1.0', 'end'))
        self.click("Показывать все")
        self.click("4. Минимум")
        self.wait_for(lambda: self.app.waiting)
        self.assertIn("N не влияет", self.app.text.get('1.0', 'end'))
        self.click("Применить")
        self.click("0. Назад")
        self.done()

    def test_three_columns_and_actions_fit_minimum_window_size(self):
        from gui_views import character_snapshot
        from player import Player
        from interface import show_battle_screen
        from encounter import create_enemy
        player = Player("Герой", None)
        self.app.update_character(character_snapshot(player))
        self.root.geometry("1040x700")
        self.root.deiconify()
        with game_io.use_backend(self.app.io):
            show_battle_screen(player, create_enemy("wolf", 1), ["Начало боя"])
        self.wait_for(lambda: self.app.last_screen["kind"] == "battle")
        self.app.show_prompt(Prompt("Выберите действие", "menu", (("1", "Атака"), ("2", "Завершить ход"))))
        self.root.update()
        left, center, right = self.app.left, self.app.battle_stage, self.app.right
        self.assertLess(left.winfo_rootx() + left.winfo_width(), center.winfo_rootx())
        self.assertLess(center.winfo_rootx() + center.winfo_width(), right.winfo_rootx())
        self.assertGreater(center.winfo_height(), 100)
        self.assertGreater(self.app.action_canvas.winfo_height(), 60)
        self.assertFalse(self.app.entry_row.winfo_ismapped())
        self.assertLessEqual(self.app.ability_panel.winfo_rooty() + self.app.ability_panel.winfo_height(),
                             self.app.action_panel.winfo_rooty())
        self.assertLess(self.app.action_panel.winfo_rooty() + self.app.action_panel.winfo_height(),
                        self.root.winfo_rooty() + self.root.winfo_height())
        self.assertLess(right.winfo_rootx() + right.winfo_width(),
                        self.root.winfo_rootx() + self.root.winfo_width())


if __name__ == "__main__":
    unittest.main()
