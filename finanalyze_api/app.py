from datetime import datetime
from typing import Any, Dict, List, Tuple, Union
from flask import Flask, Response, request, jsonify
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

@app.route("/submit-pdf", methods=['POST'])
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
        logging.info("Start of PDF to XLSX conversion using ConvertApi")
        xlsx_data = convert_pdf_to_xlsx(file)
        logging.info("Conversion result from ConvertApi: %s", xlsx_data)
        logging.info("End of PDF to XLSX conversion using ConvertApi")
    except Exception as e:
        logging.error("Error in PDF to XLSX conversion using ConvertApi: %s", e)
        return jsonify_error("Error in PDF to XLSX conversion using ConvertApi", 500)
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
    if isinstance(user_id, Tuple):  # Check if an error response was returned
        return user_id  # Return the error response directly
    # Query transactions for the user
    transactions = db.query_transactions_for_user(user_id)
    return jsonify(transactions), 200

@app.route("/categories", methods=['GET'])
def get_categories_for_user() -> Tuple[Dict[str, Any], int]:
    # Get userId from request args
    user_id = get_user_id_from_request()
    if isinstance(user_id, Tuple):  # Check if an error response was returned
        return user_id  # Return the error response directly
    # Query categories for the dashboard
    categories = db.query_categories_for_dashboard(user_id)
    return jsonify(categories), 200

@app.route("/transactions-by-category", methods=['GET'])
def get_transactions_by_category_for_user():
    # Get userId and category from request args
    user_id = get_user_id_from_request()
    if isinstance(user_id, Tuple):  # Check if an error response was returned
        return user_id  # Return the error response directly
    category = request.args.get('category')
    if not category:
        return jsonify_error("Category is missing or invalid", 400)
    # Fetch transactions for the given user and category
    transactions = db.query_transactions_bycategory(user_id, category)
    if not transactions:
        return jsonify_error("No transactions found for the given category and user", 404)
    return jsonify(transactions), 200

@app.route("/transactions-confirm", methods=['POST'])
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
    # Convert transDate for each transaction in the list
    for transaction in transactions:
        transaction["transDate"] = convert_trans_date(transaction["transDate"])
    # Filter transactions where 'userConfirm' = True
    confirmed_transactions = [transaction for transaction in transactions if transaction.get('userConfirm', True)]
    # If there are confirmed transactions, update the transactions  entirely
    if confirmed_transactions:
        db.confirm_transactions_for_user(confirmed_transactions, True)
    # Update all transactions to 'userConfirm' = True
    db.confirm_transactions_for_user(transactions, False)
    return jsonify({"message": "Transactions saved successfully"}), 200

@app.route("/transactions-unconfirm-test", methods=['GET']) # For testing
def unconfirm_transactions_for_user_test():
    # Update all transactions to userConfirm=False (unconfirm)
    db.unconfirm_transactions_for_user_test()
    return jsonify({"message": "Transactions unconfirmed successfully"}), 200

@app.route("/transactions-confirm-test", methods=['GET']) # For testing
def confirm_transactions_for_user_test():
    # Update all transactions to userConfirm=False (unconfirm)
    db.confirm_transactions_for_user_test()
    return jsonify({"message": "Transactions confirmed successfully"}), 200

@app.route("/transactions-for-dashboard", methods=['GET'])
def get_transactions_for_dashboard():
    # Get userId from request args
    user_id = get_user_id_from_request()
    if isinstance(user_id, Tuple):  # Check if an error response was returned
        return user_id  # Return the error response directly
    # Create a query against the collection
    transactions = db.query_transactions_for_dashboard(user_id)
    return jsonify(transactions), 200

@app.route("/transactions-for-piechart-by-category", methods=['GET'])
def get_transactions_for_piechart_by_category():
    # Get userId from request args
    user_id = get_user_id_from_request()
    if isinstance(user_id, Tuple):  # Check if an error response was returned
        return user_id  # Return the error response directly
    # Create a query against the collection
    transactions = db.query_transactions_for_piechart(user_id)
    return jsonify(transactions), 200

###### Helper functions ######

def get_user_id_from_request() -> Union[int, Response]:
    """Utility function to retrieve and validate the userId from request args."""
    user_id = request.args.get('user_id', type=int)
    if user_id is None:
        return jsonify_error("User Id is missing or invalid", 400)
    return user_id

def process_xlsx_data(xlsx_data):
    """Extracts data from XLSX and generates Gemini categories & data by page."""
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

def jsonify_error(message: str, status_code: int) -> Tuple[Response, int]:
    """Returns a standardized error JSON response."""
    response = {
        "success": False,
        "error": {
            "message": message,
            "status_code": status_code
        }
    }
    return jsonify(response), status_code

# Function to convert transDate to datetime
def convert_trans_date(date_str):
    try:
        # First, try ISO format (e.g., '2026-07-02T16:00:00.000Z') - from changed dates
        return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
    except ValueError:
        # If ISO format fails, try RFC 1123 format (e.g., 'Sun, 11 Feb 2024 00:00:00 GMT') - from unchanged dates
        return datetime.strptime(date_str, "%a, %d %b %Y %H:%M:%S GMT")

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=port, debug=True)