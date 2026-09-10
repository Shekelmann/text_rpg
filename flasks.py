"""Dedicated flask charges; backpack capacity and special consumables are separate."""


class FlaskStock:
    def __init__(self):
        self._charges = []

    @property
    def count(self):
        return len(self._charges)

    @property
    def restore_amount(self):
        return self._charges[0].restore_amount if self._charges else None

    @property
    def items(self):
        return tuple(self._charges)

    def add(self, charge):
        if charge in self._charges:
            return False
        self._charges.append(charge)
        return True

    def remove(self, charge):
        if charge not in self._charges:
            return False
        self._charges.remove(charge)
        return True

    def use(self, player):
        if not self._charges or not self._charges[0].use(player):
            return False
        self._charges.pop(0)
        return True
