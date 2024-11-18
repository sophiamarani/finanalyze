from typing import Any, Dict, List, Tuple
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import os
from constants import allowed_file, gemini_prompt, error_convertapi_convertpdftoexcel
from db import Database
from convert import convert_pdf_to_xlsx
from gemini import GeminiProcessor
from excel import ExcelProcessor
from user import User
from bank import BankStatementProcessor
from firebase_admin import credentials
import logging

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

# Set up structured logging
logging.basicConfig(level=logging.INFO)

@app.route("/submitPdf", methods=['POST'])
def convert_pdf_to_data():
    # Check if file is in the request
    file = request.files.get('file')
    if not file or file.filename == '':
        return jsonify_error("No file provided", 400)
    # Check if file type is allowed
    if not allowed_file(file.filename):
        return jsonify_error("Wrong file format", 415)
    # Convert PDF to XLSX
    try:
        logging.info("Starting PDF to XLSX conversion using ConvertApi")
        xlsx_data = convert_pdf_to_xlsx(file)
        logging.info("Conversion result from ConvertApi: %s", xlsx_data)
    except Exception as e:
        logging.error(f"{error_convertapi_convertpdftoexcel}: {e}")
        return jsonify_error(error_convertapi_convertpdftoexcel, 500)
    # Process XLSX data
    try:
        tabledata_dict_by_page, gemini_categories = process_xlsx_data(xlsx_data)
    except KeyError as e:
        logging.error("XLSX data missing expected key: %s", e)
        return jsonify_error("Invalid XLSX data structure", 500)
    except Exception as e:
        logging.error("Error processing XLSX data: %s", e)
        return jsonify_error("Failed to process XLSX data", 500)
    # Get userId
    user_id = user.get_user_id()
    # Append categories and save data to DB
    try:
        tabledata_df_by_page = bankStatementProcessor.append_categories_to_tabledata_df(tabledata_dict_by_page, gemini_categories)
        db.save_to_db(tabledata_df_by_page, user_id)
        transactions = db.query_transactions_for_user_to_confirm(user_id)
        return jsonify(transactions), 200
    except Exception as e:
        logging.error("Error saving or retrieving transactions: %s", e)
        return jsonify_error("Database operation failed to get transactions for user to confirm", 500)

@app.route("/transactions", methods=['GET'])
def get_transactions_for_user() -> Tuple[Dict[str, Any], int]:
    # Get userId from request args
    user_id = get_user_id_from_request()
    # Query transactions for the user
    transactions = query_transactions_for_user(user_id)
    return jsonify(transactions), 200

@app.route("/categories", methods=['GET'])
def get_categories_for_user() -> Tuple[Dict[str, Any], int]:
    # Get userId from request args
    user_id = get_user_id_from_request()
    # Query categories for the dashboard
    categories = query_categories_for_dashboard(user_id)
    return jsonify(categories), 200

@app.route("/transactionsByCategory", methods=['GET'])
def get_transactions_by_category_for_user():
    # Get userId and category from request args
    user_id = get_user_id_from_request()
    category = request.args.get('category')
    if not category:
        return jsonify_error("Category is missing or invalid", 400)
    # Fetch transactions for the given user and category
    transactions = db.query_transactions_bycategory(user_id, category)
    if not transactions:
        return jsonify_error("No transactions found for the given category and user", 404)
    return jsonify(transactions), 200

@app.route("/transactionsConfirm", methods=['POST'])
def confirm_transactions_for_user():
    # Get transactions from body of request
    transactions = request.get_json(silent=True)
    # Check if transactions were provided
    if not transactions:
        return jsonify_error("No transactions provided", 404)
    # Validate transactions
    invalid_transactions = [transaction for transaction in transactions if not bankStatementProcessor.is_valid_transaction(transaction)]
    if invalid_transactions:
        return jsonify_error("Invalid transactions provided", 415)
    # Filter transactions where 'userConfirm' = True
    confirmed_transactions = [transaction for transaction in transactions if transaction.get('userConfirm', True)]
    # If there are confirmed transactions, update the transactions  entirely
    if confirmed_transactions:
        db.confirm_transactions_for_user(confirmed_transactions, True)
    # Update all transactions to 'userConfirm' = True
    db.confirm_transactions_for_user(transactions, False)
    return jsonify({"message": "Transactions saved successfully"}), 200

@app.route("/transactionsUnconfirmTest", methods=['GET']) # For testing
def unconfirm_transactions_for_user_test():
    # Update all transactions to userConfirm=False (unconfirm)
    db.unconfirm_transactions_for_user_test()
    return jsonify({"message": "Transactions unconfirmed successfully"}), 200

@app.route("/transactionsConfirmTest", methods=['GET']) # For testing
def confirm_transactions_for_user_test():
    # Update all transactions to userConfirm=False (unconfirm)
    db.confirm_transactions_for_user_test()
    return jsonify({"message": "Transactions confirmed successfully"}), 200

@app.route("/transactionsForDashboard", methods=['GET'])
def get_transactions_for_dashboard():
    # Get userId from request args
    user_id = get_user_id_from_request()
    # Create a query against the collection
    transactions = db.query_transactions_for_dashboard(user_id)
    return jsonify(transactions), 200

@app.route("/transactionsForPieChartByCategory", methods=['GET'])
def get_transactions_for_piechart_by_category():
    # Get userId from request args
    user_id = get_user_id_from_request()
    # Create a query against the collection
    transactions = db.query_transactions_for_piechart(user_id)
    return jsonify(transactions), 200

###### Helper functions ######

def get_user_id_from_request():
    """Utility function to retrieve and validate the userId from request args."""
    user_id = request.args.get('userId', type=int)
    if user_id is None:
        return jsonify_error("User Id is missing or invalid", 400)
    return user_id

def process_xlsx_data(xlsx_data):
    """Extracts data from XLSX and generates Gemini categories."""
    tabledata_dict_by_page = []
    gemini_categories = ""

    # Validate presence of Files key
    files = xlsx_data.get('Files')
    if not files:
        raise KeyError("Files key is missing or empty in XLSX data")

    # Process each file in Files
    for file in files:
        url = file.get('Url')
        if not url:
            raise ValueError("File entry does not contain XLSX URL")
        
        # Load and process Excel data
        excel_file = excelProcessor.load_excel(url)
        sheet_names = excelProcessor.get_sheet_names(excel_file)
        
        for sheet in sheet_names:
            description_list, tabledata_dict = excelProcessor.convert_sheet_to_(sheet, excel_file)
            tabledata_dict_by_page.append(tabledata_dict)

            # Generate Gemini categories for each sheet (page)
            gemini_response = model.generate_content(gemini_prompt + "\n" + description_list)
            gemini_categories += gemini_response.text.lower() + "\n-next page-\n"
    
    return tabledata_dict_by_page, gemini_categories

def jsonify_error(message, status_code):
    """Returns a standardized error JSON response."""
    return jsonify({"error": message}), status_code

def query_transactions_for_user(user_id: int) -> List[Dict[str, Any]]:
    """Query the transactions for a specific user from the database."""
    return db.query_transactions_for_user(user_id)

def query_categories_for_dashboard(user_id: int) -> List[str]:
    """Query the categories for a specific user's dashboard from the database."""
    return db.query_categories_for_dashboard(user_id)

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=port, debug=True)