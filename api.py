from flask import Flask, request, jsonify
import stripe
import requests
import json
from datetime import datetime

app = Flask(__name__)

# ============ CONFIG ============
# Stripe (Test Mode)
stripe.api_key = "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"  # CHANGE THIS

# Shopify (Test Mode)
SHOPIFY_STORE = "teststrore-123.myshopify.com"  # tera development store  # CHANGE THIS
SHOPIFY_TOKEN = "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"  # CHANGE THIS
# ================================

# Official test cards (always work - no real charge)
TEST_CARDS = {
    "4242424242424242": {"brand": "Visa", "type": "credit"},
    "5555555555554444": {"brand": "Mastercard", "type": "credit"},
    "378282246310005": {"brand": "Amex", "type": "credit"},
    "6011111111111117": {"brand": "Discover", "type": "credit"},
    "4000002500003155": {"brand": "Visa", "type": "3D Secure"}
}

def parse_card(card_str):
    """Parse CC|MM|YY|CVV format"""
    try:
        parts = card_str.split('|')
        if len(parts) != 4:
            return None
        return {
            "number": parts[0].strip(),
            "month": int(parts[1].strip()),
            "year": int(parts[2].strip()),
            "cvv": parts[3].strip()
        }
    except:
        return None

@app.route('/stripe-check', methods=['GET'])
def stripe_check():
    """Stripe payment check (test mode)"""
    cc = request.args.get('cc', '')
    
    card_data = parse_card(cc)
    if not card_data:
        return jsonify({
            "Response": "❌ Invalid format. Use: CC|MM|YY|CVV",
            "Price": "-",
            "Gateway": "Stripe",
            "Status": "Error"
        })
    
    try:
        # Check if it's a valid test card
        card_num = card_data['number'][:16]
        
        if card_num not in TEST_CARDS:
            return jsonify({
                "Response": "⚠️ TEST MODE ONLY!\n\nUse Stripe test cards:\n4242424242424242 (Visa)\n5555555555554444 (Mastercard)\n378282246310005 (Amex)",
                "Price": "-",
                "Gateway": "Stripe",
                "Status": "Test card required"
            })
        
        # Create payment intent (test mode - no real charge)
        intent = stripe.PaymentIntent.create(
            amount=1000,
            currency='usd',
            payment_method_types=['card'],
            payment_method_data={
                'type': 'card',
                'card': {
                    'number': card_data['number'],
                    'exp_month': card_data['month'],
                    'exp_year': card_data['year'],
                    'cvc': card_data['cvv'],
                }
            },
            confirm=True,
            confirmation_method='manual',
        )
        
        return jsonify({
            "Response": f"✅ STRIPE TEST SUCCESS! 💎\nCard: {TEST_CARDS[card_num]['brand']}\nIntent ID: {intent.id}\nStatus: {intent.status}",
            "Price": "$10.00",
            "Gateway": "Stripe (Test)",
            "Status": "Charged"
        })
        
    except stripe.error.CardError as e:
        return jsonify({
            "Response": f"❌ Card Error: {e.error.message}",
            "Price": "-",
            "Gateway": "Stripe",
            "Status": "Declined"
        })
    except Exception as e:
        return jsonify({
            "Response": f"❌ Error: {str(e)}",
            "Price": "-",
            "Gateway": "Stripe",
            "Status": "Error"
        })

@app.route('/shopify-check', methods=['GET'])
def shopify_check():
    """Shopify checkout check (test mode)"""
    cc = request.args.get('cc', '')
    site = request.args.get('url', '')
    
    card_data = parse_card(cc)
    if not card_data:
        return jsonify({
            "Response": "❌ Invalid format. Use: CC|MM|YY|CVV",
            "Price": "-",
            "Gateway": "Shopify",
            "Status": "Error"
        })
    
    try:
        # First, get a product from the store
        headers = {
            "X-Shopify-Access-Token": SHOPIFY_TOKEN,
            "Content-Type": "application/json"
        }
        
        # Get products (test mode)
        products_url = f"https://{SHOPIFY_STORE}/admin/api/2024-01/products.json"
        products_res = requests.get(products_url, headers=headers)
        
        if products_res.status_code != 200:
            return jsonify({
                "Response": "⚠️ Shopify store not configured properly. Use development store.",
                "Price": "-",
                "Gateway": "Shopify",
                "Status": "Config Error"
            })
        
        products = products_res.json().get('products', [])
        
        if not products:
            return jsonify({
                "Response": "⚠️ No products found. Add a product to your development store first.",
                "Price": "-",
                "Gateway": "Shopify",
                "Status": "No products"
            })
        
        # Use first product for testing
        variant_id = products[0]['variants'][0]['id']
        
        # Create draft order (test mode)
        order_data = {
            "draft_order": {
                "line_items": [{
                    "variant_id": variant_id,
                    "quantity": 1
                }],
                "email": "test@example.com",
                "shipping_address": {
                    "first_name": "Test",
                    "last_name": "User",
                    "address1": "123 Test St",
                    "city": "Portland",
                    "province": "OR",
                    "country": "US",
                    "zip": "04101",
                    "phone": "555-555-5555"
                }
            }
        }
        
        draft_url = f"https://{SHOPIFY_STORE}/admin/api/2024-01/draft_orders.json"
        draft_res = requests.post(draft_url, headers=headers, json=order_data)
        
        if draft_res.status_code == 201:
            draft = draft_res.json().get('draft_order', {})
            return jsonify({
                "Response": f"✅ SHOPIFY TEST SUCCESS! 💎\nDraft Order ID: {draft.get('id')}\nStatus: {draft.get('status')}\nNote: This is TEST MODE - no real charge",
                "Price": f"${products[0].get('variants', [{}])[0].get('price', '0')}",
                "Gateway": "Shopify (Test)",
                "Status": "Success"
            })
        else:
            return jsonify({
                "Response": f"❌ Shopify error: {draft_res.text[:100]}",
                "Price": "-",
                "Gateway": "Shopify",
                "Status": "Error"
            })
            
    except Exception as e:
        return jsonify({
            "Response": f"❌ Error: {str(e)}",
            "Price": "-",
            "Gateway": "Shopify",
            "Status": "Error"
        })

@app.route('/check', methods=['GET'])
def check_all():
    """Check both Stripe and Shopify"""
    cc = request.args.get('cc', '')
    gateway = request.args.get('gateway', 'both')
    
    if gateway == 'stripe':
        return stripe_check()
    elif gateway == 'shopify':
        return shopify_check()
    else:
        # Both gateways
        stripe_result = json.loads(stripe_check().get_data())
        shopify_result = json.loads(shopify_check().get_data())
        
        return jsonify({
            "stripe": stripe_result,
            "shopify": shopify_result
        })

@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        "status": "alive",
        "gateways": ["stripe", "shopify"],
        "mode": "test_only"
    })

if __name__ == '__main__':
    print("="*50)
    print("🚀 YOUR API IS RUNNING!")
    print("="*50)
    print("\n📝 Test Commands:")
    print("http://localhost:5000/health")
    print("http://localhost:5000/stripe-check?cc=4242424242424242|12|2028|123")
    print("http://localhost:5000/shopify-check?cc=4242424242424242|12|2028|123")
    print("\n⚠️ MODE: TEST ONLY - No real charges")
    print("="*50)
    
    app.run(host='0.0.0.0', port=5000, debug=True)
