import requests

# Force send a negative number
payload = {"item": "apple", "quantity": -100}

try:
    print("Sending Manual Attack: quantity = -100")
    response = requests.post("http://localhost:8000/buy", json=payload)
    print(f"Server Response: {response.json()}")

    # Check Wallet
    wallet = requests.get("http://localhost:8000/wallet").json()
    print(f"Current Wallet: {wallet}")
except Exception as e:
    print(f"Error: {e}")
