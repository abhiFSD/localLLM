import csv
import xlsxwriter
import os
import logging
from datetime import datetime
import argparse
import requests

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class OllamaClient:
    def __init__(self, base_url="http://localhost:11434"):
        self.base_url = base_url

    def generate(self, prompt, model="llama3.1:8b", stream=False):
        url = f"{self.base_url}/api/generate"
        
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": stream
        }

        response = requests.post(url, json=payload)
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Error: {response.status_code}, {response.text}")

def parse_bank_statement(file_path):
    logger.info(f"Starting to parse bank statement from file: {file_path}")
    
    account_details = {}
    transactions = []
    transaction_start_row = None
    
    with open(file_path, 'r', newline='', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile)
        for row_index, row in enumerate(reader):
            if row and row[0] == 'Txn Date':
                transaction_start_row = row_index
                break
            elif row and ':' in row[0]:
                key, value = row[0].split(':', 1)
                account_details[key.strip()] = row[1].strip() if len(row) > 1 else ''
                logger.debug(f"Extracted account detail: {key.strip()} = {account_details[key.strip()]}")
    
    if transaction_start_row is None:
        logger.error("Could not find transaction data in the file")
        raise ValueError("Could not find transaction data in the file")
    
    # Extract transactions
    with open(file_path, 'r', newline='', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile)
        for row_index, row in enumerate(reader):
            if row_index > transaction_start_row:
                if row and row[0]:  # Ensure it's not an empty row
                    transaction = [cell.strip() for cell in row[:7]]  # Take first 7 columns and strip whitespace
                    transactions.append(transaction)
                    logger.debug(f"Parsed transaction: {transaction}")
    
    logger.info(f"Parsed {len(transactions)} transactions")
    return account_details, transactions

def categorize_transaction(client, model, transaction):
    txn_date, value_date, description, ref_no, debit, credit, balance = transaction

    prompt = f"""As an AI financial assistant, categorize the following bank transaction and provide a brief explanation:

Transaction Date: {txn_date}
Description: {description}
Debit: {debit}
Credit: {credit}

Please categorize this transaction into one of the following categories:
1. Income
2. Housing
3. Transportation
4. Food
5. Utilities
6. Insurance
7. Medical & Healthcare
8. Savings & Investments
9. Personal Spending
10. Recreation & Entertainment
11. Miscellaneous

Provide your response in the following format:
Category: [category number]
Explanation: [brief explanation]

"""

    logger.info(f"Sending transaction to model for categorization: {description}")
    try:
        response = client.generate(prompt, model=model)
        category_response = response['response'].strip()

        # Split the response into lines and remove any empty lines
        category_lines = [line.strip() for line in category_response.split('\n') if line.strip()]

        # Initialize category and explanation
        category = "Uncategorized"
        explanation = "No explanation provided"

        # Try to extract category and explanation
        for line in category_lines:
            if line.lower().startswith("category:"):
                category = line.split(":", 1)[1].strip()
            elif line.lower().startswith("explanation:"):
                explanation = line.split(":", 1)[1].strip()

        # If we didn't find a category or explanation, use the whole response
        if category == "Uncategorized" and explanation == "No explanation provided":
            explanation = category_response

        logger.info(f"Categorized transaction: Category = {category}, Explanation = {explanation}")
        return category, explanation

    except Exception as e:
        logger.error(f"Error categorizing transaction: {e}")
        return "Error", f"Failed to categorize: {str(e)}"

def process_file(input_file, output_folder, model):
    client = OllamaClient()

    logger.info(f"Processing file: {input_file}")
    try:
        account_details, transactions = parse_bank_statement(input_file)
    except Exception as e:
        logger.error(f"Error parsing file: {e}")
        return

    start_date = account_details.get('Start Date', 'Unknown')
    end_date = account_details.get('End Date', 'Unknown')
    output_file = os.path.join(output_folder, f"processed_statement_{start_date}_{end_date}.xlsx")
    workbook = xlsxwriter.Workbook(output_file)
    worksheet = workbook.add_worksheet()

    # Write account details
    row = 0
    for key, value in account_details.items():
        worksheet.write(row, 0, key)
        worksheet.write(row, 1, value)
        row += 1

    row += 1  # Add an empty row for separation

    # Write transaction headers
    headers = ['Txn Date', 'Value Date', 'Description', 'Ref No./Cheque No.', 'Debit', 'Credit', 'Balance', 'Category', 'Explanation']
    for col, header in enumerate(headers):
        worksheet.write(row, col, header)
    row += 1

    # Process each transaction individually
    for transaction in transactions:
        logger.info(f"Processing transaction: {transaction[2]}")  # Log description
        try:
            category, explanation = categorize_transaction(client, model, transaction)
        except Exception as e:
            logger.error(f"Error processing transaction: {e}")
            category, explanation = "Error", f"Failed to process: {str(e)}"
        
        # Write the transaction data and the new categorization
        try:
            worksheet.write_row(row, 0, transaction + [category, explanation])
        except Exception as e:
            logger.error(f"Error writing to Excel: {e}")
            worksheet.write_row(row, 0, transaction + ["Error writing", str(e)])
        
        row += 1
        
        # Save the workbook after each transaction
        try:
            workbook.close()
            workbook = xlsxwriter.Workbook(output_file)
            worksheet = workbook.get_worksheet_by_name('Sheet1')
        except Exception as e:
            logger.error(f"Error saving workbook: {e}")
            # If we can't save, create a new workbook
            output_file = os.path.join(output_folder, f"processed_statement_{start_date}_{end_date}_{row}.xlsx")
            workbook = xlsxwriter.Workbook(output_file)
            worksheet = workbook.add_worksheet()

    workbook.close()
    logger.info(f"Processing complete. File saved as {output_file}")

def main():
    parser = argparse.ArgumentParser(description="Process bank statements using Ollama API")
    parser.add_argument("--input", required=True, help="Path to the input file")
    parser.add_argument("--output", required=True, help="Path to the output folder")
    parser.add_argument("--model", default="llama3.1:8b", help="Model to use for categorization")
    parser.add_argument("--log", default="info", choices=["debug", "info", "warning", "error"], help="Logging level")
    args = parser.parse_args()

    # Set logging level
    logger.setLevel(getattr(logging, args.log.upper()))

    if not os.path.exists(args.output):
        os.makedirs(args.output)

    process_file(args.input, args.output, args.model)

if __name__ == "__main__":
    main()