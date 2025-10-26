from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse

app = Flask(__name__)

# Sample menu (item: price per unit)
MENU = {
    "pizza": 10.00,
    "soda": 2.00,
    "burger": 8.00,
    "fries": 3.00
}

# Store orders in memory (list of dictionaries)
orders = []

def parse_order(user_msg):
    """Parse user message to extract items and quantities."""
    user_msg = user_msg.lower().strip()
    if user_msg == "view menu":
        return {"action": "view_menu"}
    
    # Check if message starts with "order"
    if not user_msg.startswith("order"):
        return {"action": "invalid", "message": "Please start your message with 'order' or use 'view menu' to see the menu."}
    
    # Remove "order" and process the rest
    order_text = user_msg[5:].strip()
    if not order_text:
        return {"action": "invalid", "message": "Please specify items to order, e.g., 'order 2 pizzas and 1 soda'."}
    
    # Split by "and" to handle multiple items
    items = order_text.split(" and ")
    order_details = []
    total_price = 0.0
    
    for item in items:
        item = item.strip()
        # Expect format like "2 pizzas" or "1 soda"
        parts = item.split()
        if len(parts) < 2:
            return {"action": "invalid", "message": f"Invalid format for item: '{item}'. Use 'quantity item', e.g., '2 pizzas'."}
        
        try:
            quantity = int(parts[0])
            item_name = " ".join(parts[1:])  # Handle multi-word items like "ice cream"
            if item_name not in MENU:
                return {"action": "invalid", "message": f"Item '{item_name}' not found in menu. Use 'view menu' to see available items."}
            if quantity <= 0:
                return {"action": "invalid", "message": "Quantity must be positive."}
            order_details.append({"item": item_name, "quantity": quantity, "price": MENU[item_name] * quantity})
            total_price += MENU[item_name] * quantity
        except ValueError:
            return {"action": "invalid", "message": f"Invalid quantity for item: '{item}'. Use a number, e.g., '2 pizzas'."}
    
    return {"action": "order", "details": order_details, "total": total_price}

@app.route("/bot", methods=["POST"])
def bot():
    # Get user message
    user_msg = request.values.get('Body', '').lower()
    
    # Create Twilio response object
    response = MessagingResponse()
    
    # Parse the user message
    result = parse_order(user_msg)
    
    if result["action"] == "view_menu":
        # Send menu
        menu_text = "📋 Menu:\n" + "\n".join([f"{item}: ${price:.2f}" for item, price in MENU.items()])
        response.message(menu_text)
    elif result["action"] == "order":
        # Store order
        order_id = len(orders) + 1
        orders.append({"order_id": order_id, "details": result["details"], "total": result["total"]})
        
        # Prepare confirmation message
        order_summary = f"✅ Order #{order_id} received!\nItems:\n"
        for item in result["details"]:
            order_summary += f"- {item['quantity']} {item['item']}(s): ${item['price']:.2f}\n"
        order_summary += f"Total: ${result['total']:.2f}"
        response.message(order_summary)
    else:
        # Invalid input
        response.message(result["message"])
    
    return str(response)

if __name__ == "__main__":
    app.run(port=5000)