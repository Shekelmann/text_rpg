from enum import Enum


class NPC:
    def __init__(self, npc_id, name, role):
        self.id = npc_id
        self.name = name
        self.role = role


class TradeResult(Enum):
    SUCCESS = "success"
    NOT_AVAILABLE = "not_available"
    NOT_ENOUGH_GOLD = "not_enough_gold"
    INVENTORY_FULL = "inventory_full"
    ITEM_NOT_OWNED = "item_not_owned"


class Merchant(NPC):
    def __init__(self, npc_id, name, assortment, item_factory):
        super().__init__(npc_id, name, role="merchant")
        self.assortment = dict(assortment)
        self._item_factory = item_factory

    def get_buy_price(self, item_id):
        return self.assortment.get(item_id)

    def get_sell_price(self, item):
        return max(1, item.price // 2)

    def get_offer_item(self, item_id):
        if item_id not in self.assortment:
            return None
        return self._item_factory(item_id)

    def get_offer_name(self, item_id):
        item = self.get_offer_item(item_id)
        return item.name if item is not None else None

    def buy_item(self, player, item_id):
        price = self.get_buy_price(item_id)
        if price is None:
            return TradeResult.NOT_AVAILABLE
        if player.gold < price:
            return TradeResult.NOT_ENOUGH_GOLD

        item = self.get_offer_item(item_id)
        if not player.inventory.add_item(item):
            return TradeResult.INVENTORY_FULL

        player.gold -= price
        return TradeResult.SUCCESS

    def sell_item(self, player, item):
        if item not in player.inventory.items:
            return TradeResult.ITEM_NOT_OWNED

        price = self.get_sell_price(item)
        if not player.inventory.remove_item(item):
            return TradeResult.ITEM_NOT_OWNED

        player.gold += price
        return TradeResult.SUCCESS
