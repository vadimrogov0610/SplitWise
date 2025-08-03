from typing import List
import numpy as np


class SplitWiseGroup:
    CURRENCY = "zł"

    def __init__(self, name_of_group: str = "Untitled group"):
        self.NameOfGroup = name_of_group
        self.ListOfMembers: List[str] = []
        self.ListOfTransaction: List[tuple] = []
        self.SettlementMatrix = None
        self.SettlementMatrixFinal = None
        self.settled: bool = True

    def add_members(self, member_names: List[str]):
        assert isinstance(member_names, list), f"{member_names} must be a list, got {type(member_names).__name__}"
        assert all(isinstance(n, str) for n in member_names), "All names must be strings"
        self.ListOfMembers.extend(member_names)
        if self.SettlementMatrix is None:
            self.SettlementMatrix = np.zeros((len(member_names), len(member_names)))
        else:
            self.SettlementMatrix = np.pad(
                self.SettlementMatrix,
                pad_width=((0, len(member_names)), (0, len(member_names))),
                mode='constant',
                constant_values=0
            )

    def add_transaction(
            self,
            description: str,
            amount: float,
            who_paid: str,
            list_of_members: List[str],
            proportions=None
    ):
        # Assertions
        assert who_paid in self.ListOfMembers, f"Add {who_paid} to the {self.NameOfGroup} first"
        assert all(
            member in self.ListOfMembers for member in list_of_members
        ), f"Add all of {', '.join(list_of_members)} to the {self.NameOfGroup} first"
        number_of_members = len(list_of_members)
        if proportions is None:
            proportions = [1 / number_of_members] * number_of_members
        assert len(proportions) == number_of_members, "Number of members should be the same as number of proportions"

        if sum(proportions) != 1:
            proportions = [x / sum(proportions) for x in proportions]
        self.ListOfTransaction.append((description, amount, who_paid, list_of_members, proportions))

        # Update matrix
        who_paid_index = self.ListOfMembers.index(who_paid)
        for member, proportion in zip(list_of_members, proportions):
            member_index = self.ListOfMembers.index(member)
            self.SettlementMatrix[member_index, who_paid_index] += amount * proportion
            self.SettlementMatrix[who_paid_index, member_index] -= amount * proportion
        self.settled = False

    def settle_up(self):
        total_debts = np.round(self.SettlementMatrix * 100).astype(int).sum(axis=1)
        self.SettlementMatrixFinal = np.zeros(self.SettlementMatrix.shape, dtype=int)
        while total_debts.any():
            min_value = total_debts.min()
            max_value = total_debts.max()
            min_index = np.argmin(total_debts)
            max_index = np.argmax(total_debts)
            total_debts[min_index] = min(min_value + max_value, 0)
            total_debts[max_index] = max(min_value + max_value, 0)
            self.SettlementMatrixFinal[min_index, max_index] -= min(max_value, -min_value)
            self.SettlementMatrixFinal[max_index, min_index] += min(max_value, -min_value)
        self.SettlementMatrixFinal = self.SettlementMatrixFinal.astype(float) / 100
        self.settled = True

    def display_group(self):
        print(f"Group: {self.NameOfGroup}\nMembers:")
        for name in self.ListOfMembers:
            print(f"* {name}")
        print()

    def display_transactions(self):
        print('List of transactions:')
        for transaction in self.ListOfTransaction:
            print(f"*  Paid {transaction[1]} {self.CURRENCY} for {transaction[0]} by {transaction[2]}")
            print(
                f"   Split between:",
                ", ".join(f'{name} ({round(100 * percent, 2)}%)' for name, percent in zip(transaction[3], transaction[4]))
            )
        print()

    def display_settlements(self):
        if not self.settled:
            self.settle_up()




a = SplitWiseGroup("Прошмандовки")
a.add_members(["Вадим", "Мороз", "Матюшенко", "Даник", "Соня", "Кристина", "Санёк", "Миша", "Даша"])
a.add_transaction("Квест", 225, "Матюшенко", ["Матюшенко", "Мороз", "Даник", "Кристина", "Соня"])
a.add_transaction("Алко", 73.58, "Матюшенко", ["Матюшенко", "Мороз", "Даник", "Кристина", "Санёк", "Миша"])
a.add_transaction("Еда", 57.56, "Матюшенко", ["Матюшенко", "Мороз", "Даник", "Кристина", "Санёк", "Миша"])
a.add_transaction("Суши", 277, "Мороз", ["Матюшенко", "Кристина", "Соня", "Даник"])

a.display_group()
a.display_transactions()
a.display_settlements()
