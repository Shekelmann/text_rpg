"""Semantic action ordering; no screen coordinates or CLI-number assumptions."""

CATEGORIES = ("hostile", "context", "interaction", "travel", "utility")
ACTION_CATEGORIES = {
    "hunt": "hostile", "attack": "hostile",
    "chest": "context", "ground_loot": "context",
    "tavern": "interaction", "rest": "interaction", "move": "travel",
    "description": "utility",
}


def action_category(action_id):
    # New contextual actions have a predictable default; prefixes opt into a
    # category without registering individual buttons in the GUI.
    prefix = action_id.split(":", 1)[0]
    if prefix == "npc":
        return "interaction"
    if prefix in CATEGORIES:
        return prefix
    return ACTION_CATEGORIES.get(action_id, "context")


def location_action_layout(choices, routes):
    ids = {key: action for action, key in routes.items()}
    groups = {category: [] for category in CATEGORIES}
    for key, label in choices:
        action = ids.get(key, key)
        if action not in ("inventory", "abilities", "loot_filter", "exit"):
            groups[action_category(action)].append((action, key, label))
    result = []
    for row, category in enumerate(CATEGORIES):
        entries = sorted(groups[category], key=lambda entry: entry[0])
        for column, (action, key, label) in enumerate(entries):
            result.append((key, label, row, column, len(entries)))
    return result
