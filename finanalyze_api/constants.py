gemini_prompt = """Categorize these bank transactions in [food, travel, apparel, transport, bills, medical expenses, subscriptions, tax, others] by providing only the categories numbered list:"""

ALLOWED_EXTENSIONS_PDF = {'pdf'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS_PDF