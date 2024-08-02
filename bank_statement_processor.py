import json
import csv
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

def read_csv_file(file_path):
    with open(file_path, 'r', newline='', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile)
        return list(reader)

# Demo JSON structure for categories, keywords, and remarks
DEFAULT_CATEGORIES = {
    "Income": {
        "keywords": ["upwork", "paypal", "dividend", "interest", "refund"],
        "remark": "Earnings, payments received, or other income (Credit transactions only)"
    },
    "Housing": {
        "keywords": ["rent", "mortgage", "repair"],
        "remark": "Rent, mortgage, home repairs, etc."
    },
    "Transportation": {
        "keywords": ["fuel", "gas", "car", "bus", "train", "uber", "lyft", "ola"],
        "remark": "Fuel, car payments, public transport, etc."
    },
    "Food": {
        "keywords": ["grocery", "restaurant", "cafe", "food", "zomato", "swigy"],
        "remark": "Groceries, dining out, etc."
    },
    "Utilities": {
        "keywords": ["electricity", "water", "gas", "internet", "phone", "jio", "airtel", "phone"],
        "remark": "Electricity, water, gas, internet, phone bills, etc."
    },
    "Insurance": {
        "keywords": ["insurance", "policy"],
        "remark": "Health, car, home, life insurance, etc."
    },
    "Medical & Healthcare": {
        "keywords": ["doctor", "hospital", "pharmacy", "medicine"],
        "remark": "Doctor visits, medications, etc."
    },
    "Savings & Investments": {
        "keywords": ["savings", "investment", "stocks", "bonds"],
        "remark": "Deposits to savings accounts, investments, etc."
    },
    "Personal Spending": {
        "keywords": ["clothing", "entertainment", "personal"],
        "remark": "Clothing, entertainment, personal care, etc."
    },
    "Recreation & Entertainment": {
        "keywords": ["movie", "sport", "hobby", "game", "netflix"],
        "remark": "Movies, sports, hobbies, etc."
    },
    "Investment": {
        "keywords": ["INDMoney"],
        "remark": "invest to stock or SIP"
    },
    "business": {
        "keywords": ["AWS"],
        "remark": "Business expenses"
    },
    "Tax": {
        "keywords": ["tax", "Income tax"],
         "remark": "TAX related expenses"
    },
    "Miscellaneous": {
        "keywords": ["random"],
        "remark": "rando small ammounts among friends"
    }
}

def load_category_keywords(json_file=None):
    if json_file:
        with open(json_file, 'r') as f:
            return json.load(f)
    else:
        return DEFAULT_CATEGORIES

def categorize_transaction(client, model, transaction, categories):
    txn_date, value_date, description, ref_no, debit, credit, balance = transaction

    # Determine the transaction type and amount
    if debit and debit.strip() != '':
        transaction_type = "Debit (Money Out)"
        amount = debit
    elif credit and credit.strip() != '':
        transaction_type = "Credit (Money In)"
        amount = credit
    else:
        transaction_type = "Unknown"
        amount = "0"

    # Check for keyword matches
    matched_category = None
    matched_remark = None
    for category, details in categories.items():
        if any(keyword.lower() in description.lower() for keyword in details['keywords']):
            matched_category = category
            matched_remark = details['remark']
            break

    prompt = f"""Analyze and categorize this bank transaction:

Date: {txn_date}
Description: {description}
Type: {transaction_type}
Amount: {amount}

{"Suggested: " + matched_category if matched_category else ""}
{"Remark: " + matched_remark if matched_remark else ""}

Categorize into ONE of: {', '.join(categories.keys())}

Rules:
1. Credit = Money In, Debit = Money Out
2. Income only for Credit transactions (earnings/payments received)
3. Never use Income for Debit transactions
4. Person-to-person transactions = Personal Spending
5. If no suitable category, use your best guess to assing one category and Explanation"

Format:
Category: [category name or "No match"]
Explanation: [brief justification]
"""

    logger.info(f"Sending transaction to model for categorization: {description}")
    try:
        response = client.generate(prompt, model=model)
        category_response = response['response'].strip()
        logger.debug(f"Raw model response: {category_response}")

        return category_response

    except Exception as e:
        logger.error(f"Error categorizing transaction: {e}")
        return f"Category: Error\nExplanation: Failed to categorize - {str(e)}"

def process_file(input_file, output_folder, model, categories):
    client = OllamaClient()

    logger.info(f"Processing file: {input_file}")
    try:
        csv_data = read_csv_file(input_file)
    except Exception as e:
        logger.error(f"Error reading file: {e}")
        return

    transaction_start_row = None
    for i, row in enumerate(csv_data):
        if row and row[0] == 'Txn Date':
            transaction_start_row = i
            break

    if transaction_start_row is None:
        logger.error("Could not find transaction data in the file")
        return

    output_file = os.path.join(output_folder, f"processed_{os.path.basename(input_file)}")
    
    with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        
        # Write header rows
        for row in csv_data[:transaction_start_row+1]:
            writer.writerow(row + ['AI Category and Explanation'])
        
        # Process and write transaction rows
        for row in csv_data[transaction_start_row+1:]:
            if row and len(row) >= 7:  # Ensure it's a valid transaction row
                try:
                    ai_remark = categorize_transaction(client, model, row[:7], categories)
                    writer.writerow(row + [ai_remark])
                except Exception as e:
                    logger.error(f"Error processing transaction: {e}")
                    writer.writerow(row + [f"Error: {str(e)}"])
            else:
                writer.writerow(row)  # Write any other rows as-is

    logger.info(f"Processing complete. File saved as {output_file}")

def main():
    parser = argparse.ArgumentParser(description="Process bank statements using Ollama API")
    parser.add_argument("--input", required=True, help="Path to the input file")
    parser.add_argument("--output", required=True, help="Path to the output folder")
    parser.add_argument("--model", default="llama3.1:8b", help="Model to use for categorization")
    parser.add_argument("--log", default="info", choices=["debug", "info", "warning", "error"], help="Logging level")
    parser.add_argument("--categories", help="Path to the JSON file containing custom categories (optional)")
    args = parser.parse_args()

    # Set logging level
    logger.setLevel(getattr(logging, args.log.upper()))

    if not os.path.exists(args.output):
        os.makedirs(args.output)

    categories = load_category_keywords(args.categories)
    process_file(args.input, args.output, args.model, categories)

if __name__ == "__main__":
    main()