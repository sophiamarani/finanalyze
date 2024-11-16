from datetime import datetime
from typing import Union
import pandas as pd

class BankStatementProcessor:
    
    # def __init__(self):
    #     self

    def convert_gemini_categories_to_dict(self, gemini_categories):
        # Split the Gemini categories text into the respective pages 
        pages = gemini_categories.strip().split('-next page-')
        categories_by_page = {}
        count = 0
        for page in pages:
            # Check if page empty
            if page.strip() == '':
                continue
            else:
                categories = []
                # Split the page into lines
                lines = page.strip().split('\n')
                for line in lines:
                    line = line.strip().split('.')
                    categories.append(line[1].strip())
            categories_by_page[count] = categories
            count+=1
        return categories_by_page
    
        # Arrange categories into dict where key=page and value=categories_list
    def append_categories_to_tabledata_df(self, tabledata_dict_by_page, gemini_categories):
        categories_by_page = self.convert_gemini_categories_to_dict(gemini_categories)
        tabledata_df_by_page = []
        for i in range(len(tabledata_dict_by_page)):
            tabledata_df = pd.DataFrame.from_dict(tabledata_dict_by_page[i])
            categories_list = categories_by_page[i]
            tabledata_df['Category'] = categories_list
            tabledata_df_by_page.append(tabledata_df)
        # Return 1 dataframe
        return pd.concat(tabledata_df_by_page, ignore_index=True)
    
    def convert_tabledata_df_to_dict(self, tabledata_df, i, user_id):
        transaction = {
            'transDate': self.convert_string_to_datetime(tabledata_df.loc[i, "Trans Date"]),
            'desc': tabledata_df.loc[i, "Description"],
            'amount': tabledata_df.loc[i, "Transaction Amount"],
            'type': "Credit" if bool(tabledata_df.loc[i, "isCredit"]) else "Debit",
            'userId': user_id,
            'category': tabledata_df.loc[i, "Category"],
            'userConfirm': False # As user has not confirmed the transactions
        }
        return transaction

    def convert_string_to_datetime(self, trans_date_str):
        # Assuming current year is appropriate for conversion
        current_year = datetime.now().year
        # Combine the current year with the provided date string
        full_date_str = f"{trans_date_str} {current_year}"
        # Create a datetime object using strptime
        date_format = "%d %b %Y"
        trans_date = datetime.strptime(full_date_str, date_format)
        return trans_date
    
    def is_valid_transaction(self, transaction):
        # Check if all required keys exist in the transaction
        required_keys = {
            "amount": Union[int, float],
            "category": str,
            "desc": str,
            "id": str,
            "transDate": str,
            "type": str,
            "userConfirm": bool,
            "userId": int
        }
        # Ensure transaction is a dictionary
        if not isinstance(transaction, dict):
            return False
        # Check if all keys are present and of the correct type
        for key, expected_type in required_keys.items():
            if key not in transaction or not isinstance(transaction[key], expected_type):
                return False
        return True
