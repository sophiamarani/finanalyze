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

3. **Run Python App**
   1. Navigate to the `finanalyze` directory:
      ```bash
      cd finanalyze
      ```
   2. Run the `app.py` file in `finanalyze_api` directory

### Areas of Improvement

| **Feature**          | **Impact**                      |
|----------------------|---------------------------------|
| **Multi-Bank Data Processing**<br><i>App is able to support data processing from multiple banks.<i> | Enables users to gain insights into their transactions across multiple banks in one unified view. |
| **Transaction Sorting Memory**<br><i>App can "remember" each user's preferred sorting method for past transactions and automatically apply the same sorting to future similar transactions.<i> | Improves user experience by personalizing transaction sorting and reducing manual effort.<br>For example, if a user recategorizes a Grab transaction from 'ride hailing' to 'transport' in one month, future Grab transactions will be categorized as 'transport'. |
| **Real-Time Mobile Notifications On Expenditure**<br><i>App has a mobile app that can provide real-time notifications of expenditures.<i> | Enhances user engagement with timely expenditure alerts for better financial tracking.<br>For example, "80% of your online shopping budget is already spent. Was it all worth it?" |
| **Bar Graph Of Spending Change** <br><i>App is able to show a bar graph on the change of spending by categories across months<i> | Visualizes the change in spending by category across months. |
| **Yearly Spending Insights In A Fun Way** <br><i>App is able to show spending habits of the year in a fun way.<i> | Provides users with insights into their yearly spending patterns to support informed financial decisions. Also encourages user engagement and promotes the app by making annual spending insights shareable and visually appealing.<br> For example, similar to Spotify Wrapped. |
