# Example Credit Card File Format

Your Excel files should have these columns (in Hebrew):

| תאריך רכישה | שם בית עסק | סכום עסקה | מטבע עסקה | סכום חיוב | מטבע חיוב | מס' שובר | פירוט נוסף |
|------------|------------|-----------|-----------|-----------|-----------|---------|-----------|
| 01/11/2024 | שופרסל    | 250.50    | ILS       | 250.50    | ILS       | 123456  |           |
| 02/11/2024 | קפה ג'ו   | 45.00     | ILS       | 45.00     | ILS       | 123457  |           |
| 03/11/2024 | פז        | 300.00    | ILS       | 300.00    | ILS       | 123458  | תדלוק     |

## Important Notes:

1. **Column names must be in Hebrew** exactly as shown above
2. **Date format**: DD/MM/YYYY or any format Excel recognizes
3. **Amount format**: Numbers with decimal point (e.g., 250.50)
4. The system will automatically categorize based on "שם בית עסק"
5. Save as .xlsx or .xls format

## Common Credit Card Export Formats

Most Israeli credit card companies provide downloads in this format:
- לאומי כארד (Leumi Card)
- ישראכרט (Isracard)
- מקס (Max)
- כאל (Cal)

Simply download your monthly statement and place it in the `input_files/` folder!
