import firebase_admin
from firebase_admin import firestore
import uuid
from google.cloud.firestore_v1.base_query import FieldFilter
from bank import BankStatementProcessor

class Database:
    def __init__(self, cred):
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
    
    def confirmTransactionsForUser(self, confirmed_transactions, isChange):
        # Create a reference to the transactions collection
        transactions_ref = self.db.collection("transactions")
        if isChange:
            for transaction in confirmed_transactions:
                transaction_ref = transactions_ref.document(transaction.get("id"))
                if transaction_ref.get().exists:
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

    def unconfirmTransactionsForUserTest(self):
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
    
    def confirmTransactionsForUserTest(self):
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

    def query_transactions_for_dashboard(self):
         # Create a reference to the transactions collection
        transactions_ref = self.db.collection("transactions")
        # Create a query against the 'transactions' collection for user which have not been confirmed
        # Assumption: only 1 user (userId=1)
        user_transactions_ref = transactions_ref.where(filter=FieldFilter("userId", "==", 1)).where(filter=FieldFilter("userConfirm", "==", True)).stream()
        transactions = []
        for transaction in user_transactions_ref:
            if transaction.exists:
                transaction_data = transaction.to_dict()
                transaction_data['id'] = transaction.id  # Include the document ID in the data
                transactions.append(transaction_data)
        return transactions
