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
        self.debts_simplified: bool = True

    def __repr__(self):
        return (f"Group `{self.NameOfGroup}` with {len(self.ListOfMembers)} members"
                f" and {len(self.ListOfTransaction)} transactions")

    def add_members(self, member_names: List[str]):
        assert isinstance(member_names, list), f"`{member_names}` must be a list, got {type(member_names).__name__}"
        assert all(isinstance(n, str) for n in member_names), "All names must be strings"
        assert all(
            name not in self.ListOfMembers for name in member_names
        ), f"Some of members already exist in `{self.NameOfGroup}`"
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

    def remove_members(self, member_names: List[str]):
        assert isinstance(member_names, list), f"`{member_names}` must be a list, got {type(member_names).__name__}"
        for member in member_names:
            if member in self.ListOfMembers:
                member_index = self.ListOfMembers.index(member)
                self.SettlementMatrix = np.delete(
                    np.delete(
                        self.SettlementMatrix, member_index, axis=0
                    ), member_index, axis=1
                )
                self.ListOfMembers.remove(member)
                self.debts_simplified = False

    def add_transaction(
            self,
            description: str,
            amount: float,
            who_paid: str,
            list_of_members: List[str],
            proportions=None
    ):
        # Assertions
        assert who_paid in self.ListOfMembers, f"Add {who_paid} to the `{self.NameOfGroup}` first"
        assert all(
            member in self.ListOfMembers for member in list_of_members
        ), f"Add all of {', '.join(list_of_members)} to the `{self.NameOfGroup}` first"
        number_of_members = len(list_of_members)
        if proportions is None:
            proportions = [1 / number_of_members] * number_of_members
        assert len(proportions) == number_of_members, "Number of members should be the same as number of proportions"
        assert description not in [transaction[0] for transaction in self.ListOfTransaction], \
            f"Transaction `{description}` already exists"

        if sum(proportions) != 1:
            proportions = [x / sum(proportions) for x in proportions]
        self.ListOfTransaction.append((description, amount, who_paid, list_of_members, proportions))

        # Update matrix
        who_paid_index = self.ListOfMembers.index(who_paid)
        for member, proportion in zip(list_of_members, proportions):
            member_index = self.ListOfMembers.index(member)
            self.SettlementMatrix[member_index, who_paid_index] += amount * proportion
            self.SettlementMatrix[who_paid_index, member_index] -= amount * proportion
        self.debts_simplified = False

    def remove_transaction(self, description: str):
        transaction_found = None
        for transaction in self.ListOfTransaction:
            if description == transaction[0]:
                transaction_found = transaction
                break
        if transaction_found is None:
            print(f"Transaction `{description}` not found")
        else:
            self.ListOfTransaction.remove(transaction_found)

            # Update matrix
            description, amount, who_paid, list_of_members, proportions = transaction_found
            who_paid_index = self.ListOfMembers.index(who_paid)
            for member, proportion in zip(list_of_members, proportions):
                member_index = self.ListOfMembers.index(member)
                self.SettlementMatrix[member_index, who_paid_index] -= amount * proportion
                self.SettlementMatrix[who_paid_index, member_index] += amount * proportion
            self.debts_simplified = False
            print(f"Transaction `{description}` successfully removed")

    def simplify_debts(self):
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
        self.debts_simplified = True

    def display_group(self):
        print(f"Group: {self.NameOfGroup}")
        if self.ListOfMembers:
            print("Members:")
            for name in self.ListOfMembers:
                print(f"* {name}")
        else:
            print("No members yet.")
        print()

    def display_transactions(self):
        if self.ListOfTransaction:
            print('List of transactions:')
            for transaction in self.ListOfTransaction:
                print(f"*  Paid {transaction[1]} {self.CURRENCY} for {transaction[0]} by {transaction[2]}")
                print(
                    f"   Split between:",
                    ", ".join(
                        f'{name} ({round(100 * percent, 2)}%)' for name, percent in zip(transaction[3], transaction[4]))
                )
        else:
            print("No transactions yet.")
        print()

    def display_debts(self):
        if not self.debts_simplified:
            self.simplify_debts()
        n = len(self.ListOfMembers)
        if not self.SettlementMatrixFinal.any():
            print("Nobody owes anything to anyone else.")
        else:
            for ind_1 in range(n):
                for ind_2 in range(n):
                    if self.SettlementMatrixFinal[ind_1, ind_2] > 0:
                        print(
                            f"* {self.ListOfMembers[ind_1]} owes {self.SettlementMatrixFinal[ind_1, ind_2]}{self.CURRENCY}"
                            f" to {self.ListOfMembers[ind_2]}"
                        )

    def settle_up(self, who_owes: str, owed_by: str, amount: float):
        # Assertions
        assert who_owes in self.ListOfMembers, f"{who_owes} must be a group member"
        assert owed_by in self.ListOfMembers, f"{owed_by} must be a group member"
        who_owes_index = self.ListOfMembers.index(who_owes)
        owed_by_index = self.ListOfMembers.index(owed_by)
        self.SettlementMatrix[who_owes_index, owed_by_index] -= amount
        self.SettlementMatrix[owed_by_index, who_owes_index] += amount
        self.debts_simplified = False
        print(f"{who_owes} paid {amount}{self.CURRENCY} to {owed_by}")
