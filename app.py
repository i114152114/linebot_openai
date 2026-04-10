from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import openai
import os
import json

app = Flask(__name__)

# ===== ENV =====
openai.api_key = os.getenv('OPENAI_API_KEY')
line_bot_api = LineBotApi(os.getenv('CHANNEL_ACCESS_TOKEN'))
handler1 = WebhookHandler(os.getenv('CHANNEL_SECRET'))

# ===== FILE LƯU COUNTER =====
COUNTER_FILE = "counter.json"

def load_counter():
    if not os.path.exists(COUNTER_FILE):
        return {"count": 0}
    with open(COUNTER_FILE, "r") as f:
        return json.load(f)

def save_counter(data):
    with open(COUNTER_FILE, "w") as f:
        json.dump(data, f)

# ===== TÍNH CÁCH CHATBOT =====
SYSTEM_PROMPT = """
Bạn là một chatbot LINE có tính cách như sau:
- Nghề nghiệp: Kỹ sư AI + trợ giảng đại học
- Phong cách: thân thiện, dễ hiểu, giải thích rõ ràng
- Chuyên môn: AI, Deep Learning, xử lý ảnh, SIFT
- Luôn trả lời bằng tiếng Việt

Cách trả lời:
1. Giải thích đơn giản trước
2. Sau đó nếu cần thì đi sâu kỹ thuật
3. Có thể đưa ví dụ minh họa
"""

# ===== ROUTE =====
@app.route('/callback', methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)

    try:
        handler1.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'

# ===== XỬ LÝ TIN NHẮN =====
@handler1.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_text = event.message.text

    # Load và tăng counter
    counter = load_counter()
    counter["count"] += 1
    save_counter(counter)

    try:
        response = openai.ChatCompletion.create(
            model="gpt-5-nano",
            temperature=1,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_text}
            ]
        )

        reply_text = response['choices'][0]['message']['content'].strip()

        # Thêm thông tin counter
        reply_text += f"\n\n📊 Bot đã trả lời {counter['count']} tin nhắn"

    except Exception as e:
        reply_text = f"Lỗi xảy ra: {str(e)}"

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply_text)
    )

# ===== RUN =====
if __name__ == '__main__':
    app.run()
