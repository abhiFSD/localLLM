import requests
import json
import argparse
import os
import base64

class OllamaClient:
    def __init__(self, base_url="http://localhost:11434"):
        self.base_url = base_url

    def generate(self, prompt, model="llava", image_path=None):
        url = f"{self.base_url}/api/generate"
        
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False
        }

        if image_path:
            with open(image_path, "rb") as image_file:
                image_data = base64.b64encode(image_file.read()).decode('utf-8')
            payload["images"] = [image_data]

        response = requests.post(url, json=payload)
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Error: {response.status_code}, {response.text}")

    def list_models(self):
        url = f"{self.base_url}/api/tags"
        response = requests.get(url)
        
        if response.status_code == 200:
            return response.json()['models']
        else:
            raise Exception(f"Error: {response.status_code}, {response.text}")

def save_to_file(content, filename="output.txt"):
    with open(filename, "w") as f:
        f.write(content)
    print(f"Output saved to {filename}")

def main():
    parser = argparse.ArgumentParser(description="Analyze images using Ollama API")
    parser.add_argument("--model", default="llava", help="Model to use for analysis (default: llava)")
    parser.add_argument("--image", required=True, help="Path to the image file to analyze")
    parser.add_argument("--prompt", default="Describe this image in detail.", help="Prompt for image analysis")
    parser.add_argument("--output", help="Output file to save the analysis results")
    args = parser.parse_args()

    client = OllamaClient()

    print("Available models:")
    try:
        models = client.list_models()
        for model in models:
            print(f"- {model['name']}")
    except Exception as e:
        print(f"Error listing models: {e}")
        return

    if not os.path.exists(args.image):
        print(f"Error: Image file '{args.image}' not found.")
        return

    print(f"\nAnalyzing image using {args.model}...")
    try:
        response = client.generate(args.prompt, model=args.model, image_path=args.image)
        print("\nAnalysis results:")
        print(response['response'])
        
        if args.output:
            save_to_file(response['response'], args.output)
        
        print("\nMetadata:")
        print(f"Total duration: {response['total_duration']} ns")
        print(f"Load duration: {response['load_duration']} ns")
        print(f"Prompt eval count: {response['prompt_eval_count']}")
        print(f"Prompt eval duration: {response['prompt_eval_duration']} ns")
        print(f"Eval count: {response['eval_count']}")
        print(f"Eval duration: {response['eval_duration']} ns")
    except Exception as e:
        print(f"An error occurred during analysis: {e}")

if __name__ == "__main__":
    main()