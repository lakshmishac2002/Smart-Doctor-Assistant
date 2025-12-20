"""
Free Notification Integration

Supports:
- Discord Webhooks (100% FREE)
- Telegram Bot (FREE)
- Console logging (fallback)
"""

import os
import requests
import json
from typing import Dict, Any, Optional
from datetime import datetime


class FreeNotificationClient:
    """Free notification client supporting multiple providers"""
    
    def __init__(self):
        """Initialize notification client"""
        self.discord_webhook_url = os.getenv("DISCORD_WEBHOOK_URL")
        self.telegram_bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.telegram_chat_id = os.getenv("TELEGRAM_CHAT_ID")
    
    def send_notification(
        self, 
        title: str, 
        message: str,
        notification_type: str = "info",
        recipient: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send notification via available provider
        
        Args:
            title: Notification title
            message: Notification message
            notification_type: "info", "success", "warning", "error"
            recipient: Optional recipient identifier
            
        Returns:
            Result dictionary
        """
        # Try Discord first (if configured)
        if self.discord_webhook_url:
            return self._send_discord(title, message, notification_type)
        
        # Try Telegram second (if configured)
        elif self.telegram_bot_token and self.telegram_chat_id:
            return self._send_telegram(title, message, notification_type)
        
        # Fallback to console logging
        else:
            return self._send_console(title, message, notification_type)
    
    def _send_discord(
        self, 
        title: str, 
        message: str,
        notification_type: str
    ) -> Dict[str, Any]:
        """
        Send notification via Discord Webhook (100% FREE)
        
        Setup:
        1. Go to Discord Server Settings → Integrations → Webhooks
        2. Create New Webhook
        3. Copy webhook URL
        4. Add to .env as DISCORD_WEBHOOK_URL
        """
        try:
            # Choose color based on type
            colors = {
                "info": 3447003,      # Blue
                "success": 3066993,   # Green
                "warning": 15105570,  # Orange
                "error": 15158332,    # Red
                "report": 9442302     # Purple
            }
            color = colors.get(notification_type, colors["info"])
            
            # Create embed
            embed = {
                "title": f"🏥 {title}",
                "description": message,
                "color": color,
                "timestamp": datetime.utcnow().isoformat(),
                "footer": {
                    "text": "Smart Doctor Assistant • FREE Discord Notifications"
                }
            }
            
            payload = {
                "embeds": [embed]
            }
            
            response = requests.post(
                self.discord_webhook_url,
                json=payload,
                timeout=10
            )
            response.raise_for_status()
            
            print(f"✅ Discord notification sent: {title}")
            return {
                "success": True,
                "provider": "Discord Webhook (FREE)",
                "message": "Notification sent successfully"
            }
            
        except Exception as e:
            print(f"❌ Discord notification error: {e}")
            return {
                "success": False,
                "error": str(e),
                "fallback": "Discord webhook failed"
            }
    
    def _send_telegram(
        self, 
        title: str, 
        message: str,
        notification_type: str
    ) -> Dict[str, Any]:
        """
        Send notification via Telegram Bot (100% FREE)
        
        Setup:
        1. Message @BotFather on Telegram
        2. Create new bot with /newbot
        3. Copy bot token
        4. Get your chat_id by messaging @userinfobot
        5. Add to .env: TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID
        """
        try:
            # Choose emoji based on type
            emojis = {
                "info": "ℹ️",
                "success": "✅",
                "warning": "⚠️",
                "error": "❌",
                "report": "📊"
            }
            emoji = emojis.get(notification_type, emojis["info"])
            
            # Format message
            text = f"{emoji} *{title}*\n\n{message}\n\n_Smart Doctor Assistant • FREE Telegram_"
            
            url = f"https://api.telegram.org/bot{self.telegram_bot_token}/sendMessage"
            payload = {
                "chat_id": self.telegram_chat_id,
                "text": text,
                "parse_mode": "Markdown"
            }
            
            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()
            
            print(f"✅ Telegram notification sent: {title}")
            return {
                "success": True,
                "provider": "Telegram Bot (FREE)",
                "message": "Notification sent successfully"
            }
            
        except Exception as e:
            print(f"❌ Telegram notification error: {e}")
            return {
                "success": False,
                "error": str(e),
                "fallback": "Telegram bot failed"
            }
    
    def _send_console(
        self, 
        title: str, 
        message: str,
        notification_type: str
    ) -> Dict[str, Any]:
        """Fallback: Log to console"""
        # Choose icon based on type
        icons = {
            "info": "ℹ️",
            "success": "✅",
            "warning": "⚠️",
            "error": "❌",
            "report": "📊"
        }
        icon = icons.get(notification_type, icons["info"])
        
        print(f"\n{'='*60}")
        print(f"{icon} NOTIFICATION: {title}")
        print(f"{'='*60}")
        print(message)
        print(f"{'='*60}\n")
        
        return {
            "success": True,
            "provider": "Console (Fallback)",
            "message": "Notification logged to console"
        }
    
    def send_doctor_report(
        self, 
        doctor_name: str,
        report_content: str
    ) -> Dict[str, Any]:
        """
        Send formatted report to doctor
        
        Args:
            doctor_name: Name of the doctor
            report_content: Report content
            
        Returns:
            Result dictionary
        """
        title = f"Daily Report for {doctor_name}"
        
        # Format report nicely
        formatted_message = f"""
**Doctor:** {doctor_name}
**Generated:** {datetime.now().strftime("%Y-%m-%d %H:%M")}

{report_content}

---
*Generated by AI-powered Smart Doctor Assistant*
        """.strip()
        
        return self.send_notification(
            title=title,
            message=formatted_message,
            notification_type="report"
        )


# Global notification client instance
notification_client = None

def get_notification_client() -> FreeNotificationClient:
    """Get or create notification client"""
    global notification_client
    if notification_client is None:
        notification_client = FreeNotificationClient()
    return notification_client
