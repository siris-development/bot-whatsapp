from app.schemas.whatsapp_response import WhatsAppMessage, WhatsAppResponse
import requests
from utils.constants import Constants

def send_to_whatsapp(message_content: str, session_id: str, phone_number_id: str, to: str):
    """Send a message to WhatsApp"""
    try:
        
        post_data = WhatsAppResponse(
            sessionId=session_id,
            phoneNumberId=phone_number_id,
            to=to,
            messages=[WhatsAppMessage(type="text", content=str(message_content))]
        )
        
        post_data_dict = post_data.model_dump()
        
        headers = {"Content-Type": "application/json"}
        resp = requests.post(
            url=f"{Constants.base_url}/whatsapp/send-message", 
            headers=headers, 
            json=post_data_dict
        )
        resp.raise_for_status()
        data = resp.json()

        return True

    except requests.exceptions.ConnectionError as e:
        return False
        
    except requests.exceptions.Timeout as e:
        return False
        
    except requests.exceptions.HTTPError as e:
        return False
        
    except requests.RequestException as e:
        return False
        
    except Exception as e:
        return False