import requests
import os
from dotenv import load_dotenv

load_dotenv()

convertapi_key=os.getenv("CONVERTAPI_KEY")
pdf_to_xlsx_url = 'https://v2.convertapi.com/convert/pdf/to/xlsx?auth=' + convertapi_key + '&StoreFile=true'

def convert_pdf_to_xlsx(file):
    files={'file':(file.filename, file.stream, file.content_type, file.headers)}
    xlsx_response = requests.post(pdf_to_xlsx_url, files=files)
    xlsx_data = xlsx_response.json()
    return xlsx_data
