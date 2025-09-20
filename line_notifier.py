# line_notifier.py

from linebot import LineBotApi
from linebot.models import TextSendMessage
from linebot.exceptions import LineBotApiError
channel_access_token='cp5vn48kAtKqVltKaZeq4aHmBR6jDAkrO3RguXnTJE3ocYFXjvTY1oybZ3f52Jo97yuW5WzEDPyRVI9IEcIm+m5nSWBjUcHtgVlwpilVLBenr6PzedOCpTUHcs7p2z5Btd82aUlTfoDNDz7sDIDRaQdB04t89/1O/w1cDnyilFU='
class LineNotifier:
    def __init__(self, channel_access_token):
        """
        初始化時，需要傳入您的 Channel Access Token
        """
        self.line_bot_api = LineBotApi(channel_access_token)

    def send_message(self, message_text):
        """
        發送廣播訊息給所有將 Bot 加為好友的人
        """
        try:
            # 使用 broadcast 方法，將訊息發送給所有好友
            self.line_bot_api.broadcast(TextSendMessage(text=message_text))
            print(">>> LINE 訊息已成功發送！")
        except LineBotApiError as e:
            print(f"錯誤：LINE 訊息發送失敗. {e.error.message}")
        except Exception as e:
            print(f"錯誤：發送過程中發生未知錯誤. {e}")