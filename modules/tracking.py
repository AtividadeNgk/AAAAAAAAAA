import requests
import json
from datetime import datetime
import pytz
import modules.manager as manager

class UTMifyTracker:
    def __init__(self, api_token, platform_name="NGKPay"):
        self.api_token = api_token
        self.platform_name = platform_name
        self.base_url = "https://api.utmify.com.br/api-credentials/orders"
        self.headers = {
            'x-api-token': api_token,
            'Content-Type': 'application/json'
        }
        self.brasilia_tz = pytz.timezone('America/Sao_Paulo')
    
    def _get_utc_time(self, dt=None):
        """Converte horário de Brasília para UTC"""
        if dt is None:
            dt = datetime.now(self.brasilia_tz)
        if dt.tzinfo is None:
            dt = self.brasilia_tz.localize(dt)
        return dt.astimezone(pytz.UTC).strftime('%Y-%m-%d %H:%M:%S')
    
    def send_order(self, order_data):
        """Envia pedido para UTMIFY"""
        try:
            response = requests.post(
                self.base_url,
                headers=self.headers,
                json=order_data,
                timeout=10
            )
            
            if response.status_code == 200:
                return {'success': True, 'data': response.json()}
            else:
                return {'success': False, 'error': response.text, 'status': response.status_code}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def create_waiting_payment(self, user_id, bot_id, plan, order_id):
        """Cria pedido com status waiting_payment (PIX gerado)"""
        # Busca dados do usuário e tracking
        tracking = manager.get_user_tracking(user_id, bot_id)
        if not tracking:
            tracking = {}
        
        # Monta o payload
        order_data = {
            "orderId": order_id,
            "platform": self.platform_name,
            "paymentMethod": "pix",
            "status": "waiting_payment",
            "createdAt": self._get_utc_time(),
            "approvedDate": None,
            "refundedAt": None,
            "customer": {
                "name": f"User {user_id}",  # Você pode melhorar isso pegando o nome real
                "email": f"{user_id}@telegram.user",
                "phone": None,
                "document": None,
                "country": "BR",
                "ip": tracking.get('ip_address')
            },
            "products": [{
                "id": f"plan_{bot_id}",
                "name": plan.get('name', 'Plano VIP'),
                "planId": None,
                "planName": None,
                "quantity": 1,
                "priceInCents": int(plan.get('value', 0) * 100)
            }],
            "trackingParameters": {
                "src": tracking.get('src'),
                "sck": tracking.get('sck'),
                "utm_source": tracking.get('utm_source'),
                "utm_campaign": tracking.get('utm_campaign'),
                "utm_medium": tracking.get('utm_medium'),
                "utm_content": tracking.get('utm_content'),
                "utm_term": tracking.get('utm_term')
            },
            "commission": {
                "totalPriceInCents": int(plan.get('value', 0) * 100),
                "gatewayFeeInCents": int(plan.get('value', 0) * 5),  # 5% de taxa
                "userCommissionInCents": int(plan.get('value', 0) * 95),
                "currency": "BRL"
            },
            "isTest": False
        }
        
        return self.send_order(order_data)
    
    def update_to_paid(self, user_id, bot_id, plan, order_id, created_at):
        """Atualiza pedido para status paid"""
        # Busca dados do usuário e tracking
        tracking = manager.get_user_tracking(user_id, bot_id)
        if not tracking:
            tracking = {}
        
        # Monta o payload
        order_data = {
            "orderId": order_id,
            "platform": self.platform_name,
            "paymentMethod": "pix",
            "status": "paid",
            "createdAt": created_at,  # Mantém a data original
            "approvedDate": self._get_utc_time(),  # Agora está pago
            "refundedAt": None,
            "customer": {
                "name": f"User {user_id}",
                "email": f"{user_id}@telegram.user",
                "phone": None,
                "document": None,
                "country": "BR",
                "ip": tracking.get('ip_address')
            },
            "products": [{
                "id": f"plan_{bot_id}",
                "name": plan.get('name', 'Plano VIP'),
                "planId": None,
                "planName": None,
                "quantity": 1,
                "priceInCents": int(plan.get('value', 0) * 100)
            }],
            "trackingParameters": {
                "src": tracking.get('src'),
                "sck": tracking.get('sck'),
                "utm_source": tracking.get('utm_source'),
                "utm_campaign": tracking.get('utm_campaign'),
                "utm_medium": tracking.get('utm_medium'),
                "utm_content": tracking.get('utm_content'),
                "utm_term": tracking.get('utm_term')
            },
            "commission": {
                "totalPriceInCents": int(plan.get('value', 0) * 100),
                "gatewayFeeInCents": int(plan.get('value', 0) * 5),
                "userCommissionInCents": int(plan.get('value', 0) * 95),
                "currency": "BRL"
            },
            "isTest": False
        }
        
        return self.send_order(order_data)