from flask import Blueprint, request, jsonify, session
from datetime import datetime
import requests

# Blueprint
whatsapp_bp = Blueprint('whatsapp_bp', __name__)

# WhatsApp Bot API Configuration
WHATSAPP_BOT_URL = "https://whatsapp-bot-557742533869.asia-south1.run.app"
WHATSAPP_BOT_KEY = "verysecret"


@whatsapp_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'service': 'whatsapp',
        'timestamp': datetime.now().isoformat()
    }), 200


@whatsapp_bp.route('/send-campaign', methods=['POST'])
def send_campaign():
    """
    Send WhatsApp campaign - just forwards to WhatsApp Bot API.
    
    Expected JSON: { "prompt": "...", "product_id": "...", "image_url": "..." }
    Returns: { "success": true, "message": "...", "notified_count": 3, ... }
    """
    try:
        # Parse request
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        prompt = data.get('prompt', '').strip()
        product_id = data.get('product_id', '').strip()
        image_url = data.get('image_url', '').strip()
        
        # Validation
        if not prompt or not product_id or not image_url:
            return jsonify({'success': False, 'error': 'prompt, product_id, and image_url are required'}), 400
        
        # Make request to WhatsApp Bot API (exactly like the curl command)
        bot_endpoint = f"{WHATSAPP_BOT_URL}/admin/send_prompt_image"
        
        print(f"🚀 Sending to WhatsApp Bot: {prompt[:50]}... | Product: {product_id}")
        
        # Send as form data with key as query param
        response = requests.post(
            bot_endpoint,
            params={'key': WHATSAPP_BOT_KEY},
            data={
                'prompt': prompt,
                'product_id': product_id,
                'image_url': image_url
            },
            timeout=30
        )
        
        # Return the response from WhatsApp Bot
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Campaign sent! Notified: {result.get('notified_count', 0)} users")
            
            return jsonify({
                'success': True,
                'message': result.get('message', ''),
                'image_url': result.get('image_url', ''),
                'notified_count': result.get('notified_count', 0),
                'status': result.get('status', 'sent')
            }), 200
        else:
            error_msg = f"WhatsApp Bot error: {response.status_code}"
            try:
                error_msg += f" - {response.json()}"
            except:
                error_msg += f" - {response.text}"
            
            print(f"❌ {error_msg}")
            return jsonify({'success': False, 'error': error_msg}), response.status_code
    
    except requests.RequestException as e:
        print(f"❌ Connection error: {e}")
        return jsonify({'success': False, 'error': f'Failed to connect: {str(e)}'}), 500
    
    except Exception as e:
        print(f"❌ Error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@whatsapp_bp.route('/generate-message', methods=['POST'])
def generate_message():
    """
    Generate AI campaign message using WhatsApp Bot's Gemini AI.
    
    Expected JSON: { "product_id": "...", "user_prompt": "15% discount..." }
    Returns: { "success": true, "message": "Generated campaign text" }
    """
    try:
        # Parse request
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        product_id = data.get('product_id', '').strip()
        user_prompt = data.get('user_prompt', '').strip()
        
        if not product_id:
            return jsonify({'success': False, 'error': 'product_id is required'}), 400
        
        # Call WhatsApp Bot to generate marketing text
        # The bot has gemini_generate_marketing() function that creates proper WhatsApp messages
        bot_endpoint = f"{WHATSAPP_BOT_URL}/admin/generate_marketing"
        
        print(f"🤖 Generating message for product: {product_id}")
        
        response = requests.post(
            bot_endpoint,
            params={'key': WHATSAPP_BOT_KEY},
            json={
                'product_id': product_id,
                'prompt': user_prompt
            },
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            generated_text = result.get('message', '')
            
            print(f"✅ Generated message: {generated_text[:100]}...")
            
            return jsonify({
                'success': True,
                'message': generated_text,
                'product_name': result.get('product_name', ''),
                'product_price': result.get('product_price', 0)
            }), 200
        else:
            # Fallback: create simple message if bot endpoint doesn't exist
            print(f"⚠️ Bot generate endpoint failed, using fallback")
            
            fallback_message = f"{user_prompt}\n\n" if user_prompt else "🎉 Special Offer!\n\n"
            fallback_message += f"Check out our amazing product!\n\n"
            fallback_message += f"📦 Product ID: {product_id}\n"
            fallback_message += f"💬 Reply to order now!"
            
            return jsonify({
                'success': True,
                'message': fallback_message,
                'product_name': '',
                'product_price': 0
            }), 200
    
    except requests.RequestException as e:
        print(f"❌ Connection error: {e}")
        # Return fallback message on error
        fallback_message = f"{data.get('user_prompt', '🎉 Special Offer!')}\n\nCheck out our product!\nReply to order now!"
        return jsonify({
            'success': True,
            'message': fallback_message,
            'product_name': '',
            'product_price': 0
        }), 200
    
    except Exception as e:
        print(f"❌ Error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
