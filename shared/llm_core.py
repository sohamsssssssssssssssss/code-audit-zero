import json
import requests
from openai import AzureOpenAI
from shared.config import settings

# ==============================================================================
# 🔑 AZURE CONFIGURATION (PASTE YOUR KEYS HERE)
# ==============================================================================

# 1. The Endpoint (Found in Azure Portal -> Keys & Endpoint)
# Example: "https://imagine-cup-mvp.openai.azure.com/"
AZURE_ENDPOINT = "https://athar-mjpuqnlv-eastus2.cognitiveservices.azure.com/"

# 2. Key 1 (Found in Azure Portal -> Keys & Endpoint)
AZURE_API_KEY = settings.AZURE_API_KEY
# 3. Deployment Name (The name you typed when you deployed gpt-4o in AI Studio)
# We agreed on "gpt-4-deploy", but check your AI Studio if you aren't sure.
DEPLOYMENT_NAME = "gpt-4-deploy"

# Standard API Version for 2024/2025
API_VERSION = "2024-02-15-preview"

# ==============================================================================
# 🧠 THE BRAIN (CLIENT SETUP)
# ==============================================================================

client = AzureOpenAI(
    azure_endpoint=AZURE_ENDPOINT,
    api_key=AZURE_API_KEY,
    api_version=API_VERSION
)

def ask_local_llm(messages):
    """
    Sends a request to the local inference server.
    """
    try:
        payload = {
            "messages": messages,
            "temperature": 0.1,
            "max_tokens": 1000
        }
        response = requests.post(settings.LOCAL_LLM_URL, json=payload, timeout=120)
        data = response.json()
        return data["choices"][0]["message"]["content"]
    except Exception as e:
        return f"ERROR_LOCAL_LLM: {str(e)}"

def ask_llm_text(system_prompt, user_prompt):
    """
    Sends a prompt to the configured LLM and returns the text response.
    """
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]
    
    if settings.LLM_PROVIDER == "local":
        return ask_local_llm(messages)
        
    try:
        response = client.chat.completions.create(
            model=DEPLOYMENT_NAME,
            messages=messages,
            temperature=0.1,
            max_tokens=2000
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"ERROR_LLM: {str(e)}"

def ask_llm_json(system_prompt, user_prompt):
    """
    Forces the LLM to return valid JSON.
    """
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]

    if settings.LLM_PROVIDER == "local":
        response_text = ask_local_llm(messages)
        try:
            # Attempt to extract JSON if LLM included conversational filler
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "{" in response_text:
                start = response_text.find("{")
                end = response_text.rfind("}") + 1
                response_text = response_text[start:end]
            return json.loads(response_text)
        except Exception as e:
            print(f"ERROR_JSON_LOCAL: {e}")
            return {}

    try:
        response = client.chat.completions.create(
            model=DEPLOYMENT_NAME,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format={ "type": "json_object" }, # This forces JSON output
            temperature=0.1
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        print(f"ERROR_JSON_LLM: {e}")
        return {}