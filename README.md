# Bank Statement Processor

This repository contains a Python script for processing bank statements using the Ollama API for transaction categorization.

## Script: bank_statement_processor.py

This script processes CSV bank statements and categorizes transactions using AI-powered analysis.

### Features:

- Reads CSV bank statements
- Categorizes transactions using the Ollama API
- Supports custom category definitions
- Outputs a new CSV file with added AI categorization and explanations

### Requirements:

- Python 3.6+
- `requests` library

Install the required library using:

```
pip install requests
```

### Usage:

```
python bank_statement_processor.py --input <input_file> --output <output_folder> [options]
```

#### Arguments:

- `--input`: Path to the input CSV file (required)
- `--output`: Path to the output folder (required)
- `--model`: Ollama model to use for categorization (default: "llama3.1:8b")
- `--log`: Logging level (choices: debug, info, warning, error; default: info)
- `--categories`: Path to a JSON file containing custom categories (optional)

#### Example:

```
python bank_statement_processor.py --input statements/march_2024.csv --output processed_statements --model llama3.1:8b --log info
```

### Custom Categories:

You can define custom categories by creating a JSON file with the following structure:

```json
{
  "Category Name": {
    "keywords": ["keyword1", "keyword2"],
    "remark": "Description of the category"
  },
  ...
}
```

Use the `--categories` option to specify the path to your custom categories file.

## Setup and Running

1. Clone this repository:
   ```
   git clone <repository_url>
   cd <repository_name>
   ```

2. Install the required library:
   ```
   pip install requests
   ```

3. Ensure you have the Ollama API running locally (default: http://localhost:11434)

4. Run the script with your bank statement:
   ```
   python bank_statement_processor.py --input path/to/your/statement.csv --output path/to/output/folder
   ```

5. Check the output folder for the processed CSV file with AI-categorized transactions.

## Notes

- The script assumes a specific format for the input CSV file. Ensure your bank statement matches this format or modify the script accordingly.
- The Ollama API should be running locally for the script to work. Adjust the `base_url` in the `OllamaClient` class if your setup differs.
- Custom category definitions can help improve categorization accuracy for your specific needs.
# localLLM
