import os
import json
from openai import AzureOpenAI

# ==============================================================================
# 🔑 AZURE CONFIGURATION (PASTE YOUR KEYS HERE)
# ==============================================================================

# 1. The Endpoint (Found in Azure Portal -> Keys & Endpoint)
# Example: "https://imagine-cup-mvp.openai.azure.com/"
AZURE_ENDPOINT = ("YOUR_AZURE_ENDPOINT")

# 2. Key 1 (Found in Azure Portal -> Keys & Endpoint)
AZURE_API_KEY = "YOUR_AZURE"
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

def ask_llm(system_role, user_prompt):
    """
    Sends a prompt to GPT-4o and returns the text response.
    Used for general reasoning and patch generation.
    """
    try:
        response = client.chat.completions.create(
            model=DEPLOYMENT_NAME,
            messages=[
                {"role": "system", "content": system_role},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.1, # Low temperature = more precise/deterministic
            max_tokens=2000
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"ERROR_LLM: {str(e)}"

def ask_llm_json(system_role, user_prompt):
    """
    Forces the LLM to return valid JSON.
    Crucial for the Red Agent to generate structured attack data.
    """
    try:
        response = client.chat.completions.create(
            model=DEPLOYMENT_NAME,
            messages=[
                {"role": "system", "content": system_role},
                {"role": "user", "content": user_prompt}
            ],
            response_format={ "type": "json_object" }, # This forces JSON output
            temperature=0.1
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        print(f"ERROR_JSON_LLM: {e}")
        return {}