import pandas as pd

class ExcelProcessor:

    # def __init__(self):
    #     self

    def clean_and_convert(self, value):
        if isinstance(value, str): # If Transaction Amount value is str
            value = value.replace('CR', '') # Remove 'CR'
            value = value.replace(',', '') # Remove comma
            return float(value) # Convert to float
        else:
            return value

    def check_for_credit(self, value):
        if isinstance(value, str): # If Transaction Amount value is str
            if 'CR' in value:
                return True
            else:
                return False
        return False

    def load_excel(self, excel_link):
        file = pd.ExcelFile(excel_link) # Load excel
        return file

    def get_sheet_names(self, excel):
        return excel.sheet_names

    def convert_sheet_to_(self, sheet, excel):
        # print(sheet)
        df = pd.read_excel(excel, sheet_name=sheet) # Get 1 sheet
        df1 = df.dropna().reset_index().drop(columns='index') # Drop rows with NaN values and reset index
        last_column_name = df1.iloc[:,-1:].columns[0] # Get last column name, 'Transaction Amount'
        # print('last_column_name should be Transaction Amount:', last_column_name)
        df1['isCredit'] = df1[last_column_name].apply(self.check_for_credit) # 'Transaction Amount' contains "CR" ? 'isCredit' = True : 'isCredit' = False
        df2 = df1
        df2[last_column_name] = df2[last_column_name].apply(self.clean_and_convert) # Apply the clean_and_convert function to the 'Transaction Amount' column
        first_column_name = df2.columns[0] # Get first column name, 'Post Date'
        # print('first_column_name should be Post Date:', first_column_name)
        df2 = df2.drop(columns=first_column_name) # Drop 'Post Date' column (1st column)
        df3 = df2
        df3.columns = ['Trans Date', 'Description', 'Transaction Amount', 'isCredit'] # Reset column names
        df3_dict = df3.to_dict()
        description_list = df3['Description'].tolist()
        # print(df3.to_string(index=False))
        # print("\ndescription_list:\n", description_list)
        return self.convert_to_numbered_list(description_list), df3_dict

    def convert_to_numbered_list(self, description_list):
        result = ""
        for idx, description_list in enumerate(description_list, start=1):
            result += f"{idx}. {description_list}\n"
        return result.strip()
