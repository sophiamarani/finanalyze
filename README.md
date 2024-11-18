# Finanalyze

**Finanalyze** is your personal finance companion designed to help you **take control of your spending** and **achieve your financial goals**.

### How It Works?

-  **Upload Your Bank Statements:** Get started by securely uploading your bank statements.

-  **Gain Finance Insights:** Receive detailed insights into your spending habits, broken down by categories.

-  **Make Informed Decisions:** Use these insights to make smarter financial choices and track your progress.

Whether you're planning for a big purchase, managing your budget, or simply trying to save more, **Finanalyze** gives you the tools you need to succeed.

### How To Set Up?

1. **Create Your `.env` File**
   - Duplicate `.env.copy` and rename it to `.env`.

2. **Configure API Keys**

   - **Gemini API Key**  
     - Visit [Gemini API Documentation](https://ai.google.dev/gemini-api/docs) to generate your API key.
     - Add your key to the `.env` file by setting `GEMINI_API_KEY`.
     - *Note:* This project uses Gemini model version 1.5 Flash.

   - **ConvertAPI Key**  
     - Go to [ConvertAPI](https://www.convertapi.com/) to generate an API key for PDF to XLSX conversions.
     - Add your key to the `.env` file by setting `CONVERTAPI_KEY`.

3. **Set Up Firebase**

   - **Firebase Admin SDK**  
     - Go to your [Firebase Console](https://console.firebase.google.com/) to generate the Firebase Admin SDK JSON file.
     - Download the file and place it in a new folder named `firebase` at the root of the project.
     - *Note:* My JSON file is named `gemini-finanalyze-firebase-adminsdk-7r9gn-87f6a7f91b.json`.