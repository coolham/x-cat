import os
from telegram import Bot
from telegram.ext import Updater, MessageHandler, Filters
from telegram.utils.request import Request
from dotenv import load_dotenv


load_dotenv()

# 替换为你的 Bot Token
token = os.environ.get("TELEGRAM_API_KEY")
channel_id = os.environ.get("TELEGRAM_CHANNEL_ID")
proxy_url = os.environ.get("TELEGRAM_PROXY")  # 从环境变量获取代理URL

PROXY = {
    'proxy_url': proxy_url,
}

# 创建带有代理设置的Bot和Updater对象
if proxy_url:
    print(f"使用代理服务器: {proxy_url}")
    # 创建 Updater 对象并配置代理
    updater = Updater(token=token, use_context=True, request_kwargs=PROXY)
else:
    print("不使用代理服务器")
    updater = Updater(token=token, use_context=True)

dispatcher = updater.dispatcher

# 定义消息处理函数
def handle_message(update, context):
    # 获取消息内容
    message = update.message
    if message and message.chat and message.chat.type == "channel":  # 确保是频道消息
        print(f"频道消息: {message.text}")
        # 在这里添加你的处理逻辑，例如保存消息、分析内容等
    elif update.channel_post:
        # 处理频道消息
        channel_post = update.channel_post
        print(f"频道消息: {channel_post.text}")

# 添加消息处理器
message_handler = MessageHandler(Filters.all, handle_message)
dispatcher.add_handler(message_handler)

# 启动机器人
print("机器人已启动，开始监视频道...")
updater.start_polling()
updater.idle()