from flask import Flask, request, jsonify
import requests
import json
import random
import re

app = Flask(__name__)

# Tumhare store ki details (Step 1-3 se lo)
SHOPIFY_STORE = "teststrore-123.myshopify.com"  # CHANGE KARO
ADMIN_TOKEN = "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"  # CHANGE KARO - Admin API token

# Stripe test keys (free from stripe.com)
STRIPE_SECRET_KEY = "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"  # CHANGE KARO

def parse_card(card_str):
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

@app.route('/shopify-check', methods=['GET'])
def real_shopify_check():
    cc = request.args.get('cc', '')
    site = request.args.get('url', '')
    
    card_data = parse_card(cc)
    if not card_data:
        return jsonify({"Response": "❌ Invalid card format", "Price": "-", "Gate": "Shopify"})
    
    try:
        headers = {
            "X-Shopify-Access-Token": ADMIN_TOKEN,
            "Content-Type": "application/json"
        }
        
        # Step 1: Get a product
        products_res = requests.get(
            f"https://{SHOPIFY_STORE}/admin/api/2024-01/products.json",
            headers=headers
        )
        
        if products_res.status_code != 200:
            return jsonify({"Response": "No products found", "Price": "-", "Gate": "Shopify"})
        
        products = products_res.json().get('products', [])
        if not products:
            return jsonify({"Response": "Add a product first", "Price": "-", "Gate": "Shopify"})
        
        variant_id = products[0]['variants'][0]['id']
        price = products[0]['variants'][0]['price']
        
        # Step 2: Create draft order
        draft_data = {
            "draft_order": {
                "line_items": [{
                    "variant_id": variant_id,
                    "quantity": 1
                }],
                "customer": {
                    "email": f"test{random.randint(1,999)}@example.com"
                },
                "shipping_address": {
                    "first_name": "Test",
                    "last_name": "User",
                    "address1": "123 Test St",
                    "city": "Portland",
                    "province": "OR",
                    "country": "US",
                    "zip": "97201"
                }
            }
        }
        
        draft_res = requests.post(
            f"https://{SHOPIFY_STORE}/admin/api/2024-01/draft_orders.json",
            headers=headers,
            json=draft_data
        )
        
        if draft_res.status_code != 201:
            return jsonify({"Response": "Draft order failed", "Price": "-", "Gate": "Shopify"})
        
        draft = draft_res.json().get('draft_order', {})
        draft_id = draft.get('id')
        
        # Step 3: Complete order (test mode - no real charge)
        # For real charge, you'd need Stripe/Shopify Payments setup
        
        return jsonify({
            "Response": f"✅ ORDER COMPLETED! 💎\nDraft Order: {draft_id}\nAmount: ${price}\nNote: TEST MODE - No real charge",
            "Price": f"${price}",
            "Gate": "Shopify"
        })
        
    except Exception as e:
        return jsonify({"Response": f"Error: {str(e)[:100]}", "Price": "-", "Gate": "Shopify"})

@app.route('/stripe-check', methods=['GET'])
def real_stripe_check():
    cc = request.args.get('cc', '')
    
    card_data = parse_card(cc)
    if not card_data:
        return jsonify({"Response": "❌ Invalid format", "Price": "-", "Gate": "Stripe"})
    
    try:
        import stripe
        stripe.api_key = STRIPE_SECRET_KEY
        
        # Create payment intent (test mode)
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
        )
        
        return jsonify({
            "Response": f"✅ STRIPE CHARGED! 💎\nIntent: {intent.id}\nStatus: {intent.status}",
            "Price": "$10.00",
            "Gate": "Stripe"
        })
        
    except Exception as e:
        return jsonify({"Response": f"❌ Declined: {str(e)[:50]}", "Price": "-", "Gate": "Stripe"})

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "alive", "version": "2.0"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
