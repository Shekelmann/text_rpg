from npc import Healer, Merchant
from objects import ITEMS, create_item


HEINRICH_ASSORTMENT = (
    "sword",
    "dagger",
    "leather_armor",
)

HEINRICH = Merchant(
    "heinrich",
    "Генрих",
    {
        item_id: ITEMS[item_id].price
        for item_id in HEINRICH_ASSORTMENT
    },
    create_item,
)

GREG = Healer("greg", "Знахарь Грег")

NPCS = {
    HEINRICH.id: HEINRICH,
    GREG.id: GREG,
}


def get_npc(npc_id):
    return NPCS.get(npc_id)
