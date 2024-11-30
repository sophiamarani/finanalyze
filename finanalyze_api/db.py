from typing import List
import firebase_admin
from firebase_admin import firestore
import uuid
from google.cloud.firestore_v1.base_query import FieldFilter
from bank import BankStatementProcessor

class Database:
    def __init__(self, cred):
        # firebase_admin.initialize_app(cred)

        try:
            firebase_admin.get_app()
        except ValueError:
            firebase_admin.initialize_app(cred)

        self.cred = cred
        self.db = firestore.client()
        self.bank = BankStatementProcessor()

    def save_to_db(self, tabledata_df, user_id):
        # Add a new doc (transaction) in collection 'transactions'
        # Each doc's id is randomly generated uuid
        for i in range(len(tabledata_df)):
            transaction = self.bank.convert_tabledata_df_to_dict(tabledata_df, i, user_id)
            self.db.collection("transactions").document(str(uuid.uuid4())).set(transaction)

    def query_transactions_for_user(self, user_id):
        # Create a reference to the transactions collection
        transactions_ref = self.db.collection("transactions")
        # Create a query against the 'transactions' collection for user
        user_transactions_ref = transactions_ref.where(filter=FieldFilter("userId", "==", user_id)).order_by("category").order_by("transDate",  direction=firestore.Query.DESCENDING).stream()
        transactions = []
        for transaction in user_transactions_ref:
            if transaction.exists:
                transaction_data = transaction.to_dict()
                transaction_data['id'] = transaction.id  # Include the document ID in the data
                transactions.append(transaction_data)
        return transactions

    def query_transactions_for_user_to_confirm(self, user_id):
        # Create a reference to the transactions collection
        transactions_ref = self.db.collection("transactions")
        # Create a query against the 'transactions' collection for user which have not been confirmed
        user_transactions_ref = transactions_ref.where(filter=FieldFilter("userId", "==", user_id)).where(filter=FieldFilter("userConfirm", "==", False)).stream()
        transactions = []
        for transaction in user_transactions_ref:
            if transaction.exists:
                transaction_data = transaction.to_dict()
                transaction_data['id'] = transaction.id  # Include the document ID in the data
                transactions.append(transaction_data)
        return transactions
    
    def query_categories_for_dashboard(self, user_id: int) -> List[str]:
        # Create a reference to the transactions collection
        transactions_ref = self.db.collection("transactions")
        # Create a query against the 'transactions' collection for user which have not been confirmed
        user_transactions_ref = transactions_ref.where(filter=FieldFilter("userId", "==", user_id)).stream()
        # Collect unique categories from the transactions
        categories = {transaction.to_dict().get('category') for transaction in user_transactions_ref if transaction.exists}
        return list(categories)
    
    def query_transactions_bycategory(self, user_id, category):
        # Create a reference to the transactions collection
        transactions_ref = self.db.collection("transactions")
        # Create a query against the 'transactions' collection for user and a specific category
        user_transactions_ref = transactions_ref.where(filter=FieldFilter("userId", "==", user_id)).where(filter=FieldFilter("category", "==", category)).stream()
        transactions = []
        for transaction in user_transactions_ref:
            if transaction.exists:
                transaction_data = transaction.to_dict()
                transaction_data['id'] = transaction.id  # Include the document ID in the data
                transactions.append(transaction_data)
        return transactions

    def confirm_transactions_for_user(self, confirmed_transactions, is_change):
        # Create a reference to the transactions collection
        transactions_ref = self.db.collection("transactions")
        if is_change:
            for transaction in confirmed_transactions:
                transaction_ref = transactions_ref.document(transaction.get("id"))
                if transaction_ref.get().exists:
                    # transaction.pop("id")
                    transaction_ref.update(transaction)
                else:
                    print(f"No such transaction with id: '{transaction.get('id')}'")
        else:
            for transaction in confirmed_transactions:
                transaction_ref = transactions_ref.document(transaction.get("id"))
                if transaction_ref.get().exists:
                    transaction_ref.update({"userConfirm": True})
                else:
                    print(f"No such transaction with id: '{transaction.get('id')}'")

    def unconfirm_transactions_for_user_test(self):
        transactions = []
        # Get all transactions
        transactions_all = self.db.collection("transactions").stream()
        for transaction in transactions_all:
            if transaction.exists:
                transaction_data = transaction.to_dict()
                transaction_data['id'] = transaction.id  # Include the document ID in the data
                transactions.append(transaction_data)
        # Unconfirm all transactions
        transactions_ref = self.db.collection("transactions")
        for transaction in transactions:
            transaction_ref = transactions_ref.document(transaction.get("id"))
            if transaction_ref.get().exists:
                transaction_ref.update({"userConfirm": False})
        return transactions

    def confirm_transactions_for_user_test(self):
        transactions = []
        # Get all transactions
        transactions_all = self.db.collection("transactions").stream()
        for transaction in transactions_all:
            if transaction.exists:
                transaction_data = transaction.to_dict()
                transaction_data['id'] = transaction.id  # Include the document ID in the data
                transactions.append(transaction_data)
        # Unconfirm all transactions
        transactions_ref = self.db.collection("transactions")
        for transaction in transactions:
            transaction_ref = transactions_ref.document(transaction.get("id"))
            if transaction_ref.get().exists:
                transaction_ref.update({"userConfirm": True})
        return transactions

    def query_transactions_for_dashboard(self, user_id):
         # Create a reference to the transactions collection
        transactions_ref = self.db.collection("transactions")
        # Create a query against the 'transactions' collection for user which have confirmed
        user_transactions_ref = transactions_ref.where(filter=FieldFilter("userId", "==", user_id)).where(filter=FieldFilter("userConfirm", "==", True)).stream()
        transactions = []
        for transaction in user_transactions_ref:
            if transaction.exists:
                transaction_data = transaction.to_dict()
                transaction_data['id'] = transaction.id  # Include the document ID in the data
                transactions.append(transaction_data)
        return transactions
    
    def query_transactions_for_piechart(self, user_id):
        # Create a reference to the transactions collection
        transactions_ref = self.db.collection("transactions")
        # Create a query against the 'transactions' collection for user
        user_transactions_ref = transactions_ref.where(filter=FieldFilter("userId", "==", user_id)).stream()
        categories = set()
        transactions = {}
        data_id = 0
        total_sum = 0
        for transaction in user_transactions_ref:
            if transaction.exists:
                transaction_data = transaction.to_dict()
                category = transaction_data['category']
                if category == "credit":
                    continue
                if category in categories:
                    data = transactions[category]
                    data['value'] += transaction_data['amount']
                    transactions[category] = data
                    total_sum += transaction_data['amount']
                else:
                    categories.add(transaction_data['category'])
                    data = {}
                    data['id'] = data_id
                    data['value'] = transaction_data['amount']
                    data['label'] = transaction_data['category']
                    data_id += 1
                    transactions[category] = data
                    total_sum += transaction_data['amount']
        
        for data in transactions.values():
            data['percentage'] = round((data['value'] / total_sum )* 100, 2)
            data['value'] = round(data['value'], 2)

        return [value for value in transactions.values()]

        # [ { id: 0, value: 12, label: 'series A' } ]
