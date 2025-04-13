import os
import sys
from pathlib import Path
from telegram.request import HTTPXRequest  # 用于设置代理
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters
from dotenv import load_dotenv
import asyncio
import telegram

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 加载环境变量
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

BOT_TOKEN = os.getenv("TELEGRAM_API_KEY")

PROXY_URL = 'http://127.0.0.1:10808'  # 修复了冒号错误

# 获取 Bot 信息
async def test_get_bot_info():
    """
    测试获取 Bot 的基本信息
    """
    request = HTTPXRequest(proxy=PROXY_URL)  # 设置代理
    bot = telegram.Bot(BOT_TOKEN, request=request)
    async with bot:
        bot_info = await bot.get_me()
        print(f"Bot Info: {bot_info}")

# 监听并打印收到的文本消息
async def test_listen_and_print_messages():
    """
    测试监听并打印收到的文本消息
    """
    app = ApplicationBuilder().token(BOT_TOKEN).request(HTTPXRequest(proxy=PROXY_URL)).build()

    async def handle_message(update: telegram.Update, context: ContextTypes.DEFAULT_TYPE):
        """
        处理收到的消息
        """
        if update.message:
            print(f"Received message: {update.message.text}")
            # 回复消息
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f"Echo: {update.message.text}"
            )

    # 添加消息处理器
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # 启动轮询
    try:
        await app.run_polling()
    except Exception as e:
        print(f"运行时错误: {e}")
    finally:
        # 确保正确关闭应用程序
        if app.running:
            await app.shutdown()
            await app.stop()

if __name__ == '__main__':
    try:
        # 检查是否有正在运行的事件循环
        try:
            loop = asyncio.get_running_loop()
            print("Running test: Get Bot Info")
            loop.run_until_complete(test_get_bot_info())
            print("Running test: Listen and Print Messages")
            loop.run_until_complete(test_listen_and_print_messages())
        except RuntimeError:
            # 如果没有运行的事件循环，则创建一个新的
            print("Running test: Get Bot Info")
            asyncio.run(test_get_bot_info())
            print("Running test: Listen and Print Messages")
            asyncio.run(test_listen_and_print_messages())
    except RuntimeError as e:
        print(f"运行时错误: {e}")