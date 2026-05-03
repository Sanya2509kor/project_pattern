import requests
from django.conf import settings
from django.urls import reverse
from threading import Thread
import logging

logger = logging.getLogger(__name__)


class TelegramNotifier:
    def __init__(self):
        self.bot_token = getattr(settings, 'TELEGRAM_BOT_TOKEN', None)
        self.chat_id = getattr(settings, 'TELEGRAM_CHAT_ID', None)
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}" if self.bot_token else None
    
    def send_message(self, message):
        """Отправляет сообщение в Telegram"""
        if not self.bot_token or not self.chat_id or not self.base_url:
            logger.warning("Telegram credentials not set")
            return False
            
        url = f"{self.base_url}/sendMessage"
        payload = {
            'chat_id': self.chat_id,
            'text': message,
            'parse_mode': 'HTML'
        }
        
        try:
            response = requests.post(url, json=payload, timeout=5)
            if response.status_code == 200:
                logger.info("Telegram message sent successfully")
                return True
            else:
                logger.error(f"Telegram API error: {response.status_code}")
                return False
        except requests.RequestException as e:
            logger.error(f"Error sending Telegram message: {e}")
            return False
    
    def send_appointment_notification(self, appointment):
        """Отправляет уведомление о новой записи"""
        message = self._format_appointment_message(appointment)
        return self.send_message(message)
    
    def _format_appointment_message(self, appointment):
        """Форматирует сообщение о новой записи"""
        colors_text = ""
        if appointment.colors.exists():
            color_names = [color.name for color in appointment.colors.all()]
            colors_text = f"\n🎨 <b>Цвета:</b> {', '.join(color_names)}"
        
        comment_text = ""
        if appointment.comment:
            comment_text = f"\n💬 <b>Комментарий:</b> {appointment.comment[:100]}"
        
        user_info = ""
        if appointment.user:
            user_info = f"\n👤 <b>Пользователь:</b> {appointment.user.username}"
        
        message = f"""
🔔 <b>НОВАЯ ЗАПИСЬ!</b>

━━━━━━━━━━━━━━━━━━━━
👤 <b>Клиент:</b> {appointment.name}
📞 <b>Телефон:</b> {appointment.phone}
📅 <b>Дата:</b> {appointment.date.date.strftime('%d.%m.%Y')}
⏰ <b>Время:</b> {appointment.time.time.strftime('%H:%M')}
💇 <b>Услуга:</b> {appointment.product.name}{colors_text}{comment_text}{user_info}
━━━━━━━━━━━━━━━━━━━━

🆔 <b>ID записи:</b> {appointment.id}
        """.strip()
        
        return message


def send_telegram_async(notifier, appointment):
    """Асинхронная отправка уведомления"""
    Thread(target=notifier.send_appointment_notification, args=(appointment,), daemon=True).start()