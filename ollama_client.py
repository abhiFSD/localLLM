import requests
import json

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

    def list_models(self):
        url = f"{self.base_url}/api/tags"
        response = requests.get(url)
        
        if response.status_code == 200:
            return response.json()['models']
        else:
            raise Exception(f"Error: {response.status_code}, {response.text}")

# Example usage
if __name__ == "__main__":
    client = OllamaClient()

    # List available models
    print("Available models:")
    models = client.list_models()
    for model in models:
        print(f"- {model['name']}")

    # Generate text
    prompt = "Tell me a short story about a robot learning to paint."
    
    try:
        response = client.generate(prompt, model="llama3.1:8b")
        print("\nGenerated response:")
        print(response['response'])
        
        print("\nMetadata:")
        print(f"Total duration: {response['total_duration']} ns")
        print(f"Load duration: {response['load_duration']} ns")
        print(f"Prompt eval count: {response['prompt_eval_count']}")
        print(f"Prompt eval duration: {response['prompt_eval_duration']} ns")
        print(f"Eval count: {response['eval_count']}")
        print(f"Eval duration: {response['eval_duration']} ns")
    except Exception as e:
        print(f"An error occurred: {e}")