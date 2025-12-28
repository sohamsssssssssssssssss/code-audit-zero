# reset_demo.py
# RUN THIS TO BREAK THE APP AGAIN FOR A LIVE DEMO

code = """from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

# Database Simulation
inventory = {
    "apple": 10,
    "banana": 5,
    "flag": 1
}

user_wallet = {
    "balance": 100
}

class PurchaseRequest(BaseModel):
    item: str
    quantity: int

@app.get("/wallet")
def get_wallet():
    return user_wallet

@app.post("/buy")
def buy_item(order: PurchaseRequest):

    # 1. Check if item exists
    if order.item not in inventory:
        raise HTTPException(status_code=404, detail="Item not found")

    # VULNERABILITY RESTORED: No checks here!
    total_cost = 10 * order.quantity 

    # 3. Check balance
    if user_wallet["balance"] < total_cost:
        raise HTTPException(status_code=400, detail="Insufficient funds")

    # 4. Transaction
    user_wallet["balance"] -= total_cost
    inventory[order.item] -= order.quantity

    return {"message": "Purchase successful", "new_balance": user_wallet["balance"]}
"""

with open("target_app/main.py", "w") as f:
    f.write(code)

print("✅ APP BROKEN. Ready for Demo!")