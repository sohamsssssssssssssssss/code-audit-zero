from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

# Database simulation
user_wallet = {"balance": 100}
inventory = {"apple": 10}
item_price = 5


class PurchaseRequest(BaseModel):
    item: str
    quantity: int


@app.get("/wallet")
def get_wallet():
    return user_wallet


@app.post("/buy")
def buy_item(order: PurchaseRequest):
    # THE VULNERABILITY: Missing check for negative quantity!
    # Logic Bug: If quantity is -1, cost is -5. Balance INCREASES.

    if order.item not in inventory:
        raise HTTPException(status_code=404, detail="Item not found")

    # SECURITY PATCH (Auto-Generated)
    if order.quantity <= 0:
        raise HTTPException(status_code=400, detail='Invalid quantity')
    # SECURITY PATCH (Auto-Generated)
    if order.quantity <= 0:
        raise HTTPException(status_code=400, detail='Invalid quantity')
    total_cost = item_price * order.quantity

    if user_wallet["balance"] < total_cost:
        raise HTTPException(status_code=400, detail="Insufficient funds")

    # Transaction
    user_wallet["balance"] -= total_cost
    inventory[order.item] -= order.quantity

    return {
        "status": "success",
        "new_balance": user_wallet["balance"],
        "message": f"Bought {order.quantity} {order.item}s"
    }