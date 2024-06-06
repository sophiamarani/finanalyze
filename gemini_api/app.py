from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import os
from constants import allowed_file, gemini_prompt
from db import Database
from convert import convert_pdf_to_xlsx
from gemini import GeminiProcessor
from excel import ExcelProcessor
from user import User
from bank import BankStatementProcessor
from firebase_admin import credentials

cred = credentials.Certificate("./firebase/gemini-finanalyze-firebase-adminsdk-7r9gn-87f6a7f91b.json")
db = Database(cred)

load_dotenv()

model = GeminiProcessor(os.getenv("GEMINI_API_KEY")).model
bankStatementProcessor = BankStatementProcessor()
excelProcessor = ExcelProcessor()
user = User(1, "test_username")

app = Flask(__name__)
CORS(app)
port = 5200

@app.route("/submitPdf", methods=['POST'])
def convert_pdf_to_data():
    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No file provided"}), 400
    if file and allowed_file(file.filename): # Allow only pdf
        try:
            # Start of converting PDF to XLSX
            print("\nStart of converting PDF to XLSX using ConvertApi")
            xlsx_data = convert_pdf_to_xlsx(file)
            print("\nConvertApi XLSX response:\n", xlsx_data)
            print("\nEnd of converting XLSX to text using ConvertApi")
            # End of converting PDF to XLSX
        except Exception as e:
            print("Error in ConvertApi converting PDF to XLSX: ", e)
            return jsonify({"error": "Error in ConvertApi converting PDF to XLSX"}), 401
        gemini_categories = ""
        tabledata_dict_by_page = []
        # Check for 'Files' (= list) in xlsx_data
        if 'Files' not in xlsx_data:
            print("Files key is not present in xlsx_data")
            return jsonify({"error": "Error in XLSX response by ConvertApi"}), 401
        else:
            if xlsx_data['Files']:
                for file in xlsx_data['Files']: # There should be only 1 file (1 excel)
                    if 'Url' in file:
                        url = file['Url']
                        excel_file = excelProcessor.load_excel(url)
                        sheet_names = excelProcessor.get_sheet_names(excel_file)
                        for sheet in sheet_names:
                            description_list, tabledata_dict = excelProcessor.convert_sheet_to_(sheet, excel_file)
                            tabledata_dict_by_page.append(tabledata_dict)
                            # For each sheet (page), generate categories using Gemini
                            gemini_response = model.generate_content(gemini_prompt + "\n" + description_list)
                            gemini_categories += gemini_response.text + "\n-next page-\n"
                    else:
                        print("File does not contain XLSX URL")
                        return jsonify({"error": "Error in XLSX response by ConvertApi"}), 401
            else:
                print("Files list is empty")
                return jsonify({"error": "Error in XLSX response by ConvertApi"}), 401
    
        print("\ngemini_categories:\n", gemini_categories)
        # Get userId
        user_id = user.get_user_id()
        # Append the Gemini categories back to tabledata_dict_by_page
        tabledata_df_by_page = bankStatementProcessor.append_categories_to_tabledata_df(tabledata_dict_by_page, gemini_categories)
        print("\ntabledata_df_by_page:\n", tabledata_df_by_page)
        # Save transactions to database for user
        db.save_to_db(tabledata_df_by_page, user_id)
        # Return the unconfirmed transactions from db
        transactions = db.query_transactions_for_user_to_confirm(user_id)
        return jsonify(transactions), 200
    return jsonify({"error": "Wrong file format"}), 415

@app.route("/transactions", methods=['GET'])
def get_transactions_for_user():
    # Get userId from request args
    user_id = request.args.get('userId')
    if not user_id or not user_id.isnumeric():
        # Return an error response if user_id is None / empty / non-numeric
        return jsonify({"error": "User Id is missing / not a number"}), 400
    # Create a query against the collection
    transactions = db.query_transactions_for_user_to_confirm(int(user_id))
    return jsonify(transactions), 200

@app.route("/transactionsConfirm", methods=['POST'])
def confirmTransactionsForUser():
    # Get transactions from body of request
    transactions = request.get_json(silent=True)
    if not transactions:
        return jsonify({"error": "No transactions provided"}), 400
    # Check on transactions
    for transaction in transactions:
        if not bankStatementProcessor.isValidTransaction(transaction):
            return jsonify({"error": "Invalid transactions provided"}), 415
    # Filter transactions where 'userConfirm' = True
    confirmed_transactions = [transaction for transaction in transactions if transaction.get('userConfirm', True)]
    if confirmed_transactions:
        db.confirmTransactionsForUser(confirmed_transactions, True)
    # Update all transactions to userConfirm=True
    db.confirmTransactionsForUser(transactions, False)
    return jsonify({"message": "Transactions saved successfully"}), 200

@app.route("/transactionsUnconfirmTest", methods=['GET']) # For testing
def unconfirmTransactionsForUserTest():
    # Update all transactions to userConfirm=False (unconfirm)
    db.unconfirmTransactionsForUserTest()
    return jsonify({"message": "Transactions unconfirmed successfully"}), 200

@app.route("/transactionsConfirmTest", methods=['GET']) # For testing
def confirmTransactionsForUserTest():
    # Update all transactions to userConfirm=False (unconfirm)
    db.confirmTransactionsForUserTest()
    return jsonify({"message": "Transactions confirmed successfully"}), 200

@app.route("/transactionsForDashboard", methods=['GET'])
def getTransactionsForDashboard():
    # Create a query against the collection
    transactions = db.query_transactions_for_dashboard()
    return jsonify(transactions), 200

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=port, debug=True)