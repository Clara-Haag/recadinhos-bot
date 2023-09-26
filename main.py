import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
from os import getenv
from functools import wraps

# formatação de logs
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# decorador para restringir o acesso de comandos a usuários autorizados
USUARIOS_AUTORIZADOS = [1456515969]
def restricted(func):
    @wraps(func)
    async def wrapped(update, context, *args, **kwargs):
        user_id = update.effective_user.id
        if user_id not in USUARIOS_AUTORIZADOS:
            await context.bot.send_message(chat_id=update.effective_chat.id, text=f"⚠ Você não está autorizado.")
            return
        return await func(update, context, *args, **kwargs)
    return wrapped

# comandos do bot
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # resposta ao comando /start
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Olá! 👋")

@restricted
async def replicar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pass

async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # resposta ao receber um comando não identificado
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Desculpe, não tenho um comando assim :(")

if __name__ == '__main__':
    application = ApplicationBuilder().token(getenv('TOKEN')).build()
    
    # criando comandos
    start_handler = CommandHandler('start', start)
    no_command_handler = MessageHandler(filters.COMMAND, unknown)

    # add comandos ao app
    application.add_handler(start_handler)
    application.add_handler(no_command_handler)
    
    application.run_polling()