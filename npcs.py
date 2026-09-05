from npc import Merchant
from objects import ITEMS, create_item


HEINRICH_ASSORTMENT = (
    "heal",
    "sword",
    "dagger",
    "leather_helmet",
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

NPCS = {
    HEINRICH.id: HEINRICH,
}


def get_npc(npc_id):
    return NPCS.get(npc_id)
