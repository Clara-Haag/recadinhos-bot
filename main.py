import logging
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove, constants
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters, ConversationHandler
from os import getenv
from functools import wraps

# formatação de logs
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# para evitar todos os métodos de serem logados
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

# decorador para restringir o acesso de comandos a usuários autorizados
USUARIOS_AUTORIZADOS = [1456515969]

# váriaveis da função replicar
CANAIS_CADASTRADOS = [-1002021874904, -4026266836]
MENSAGEM, ASSINATURA = range(2)
recado = {'titulo': "RECADO IMPORTANTE!",'conteudo': '', 'Assinatura': 'Att. a direção'}

# imagens dos horários
HORARIOS = {'3infoA' : './horarios/horario-3infoA.png',
            '2infoA' : './horarios/horario-2infoA.png',
            '1infoA' : './horarios/horario-1infoA.png'}

def restricted(func):
    # função de restrição de comandos
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

async def registrar_canal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # comando de registro de canais
    id_canal = update.message.text.replace("/registrar_canal ", "")
    id_canal = int(id_canal)
    CANAIS_CADASTRADOS.append(id_canal)
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Canal registrado!")

async def ver_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text=f'O ID deste grupo é: {update.effective_chat.id}\nDICA: utilize este número no comando /registrar_canal para entrar na lista de canais do bot ;)')

async def ver_horario(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # comando para ver horários
    usuario = update.message.from_user
    turma = update.message.text.replace("/ver_horario ", "")
    for horario in HORARIOS.keys():
        if horario == turma:
            imagem = HORARIOS[horario]
            await context.bot.send_photo(chat_id= usuario.id, photo=open(imagem, 'rb'))

# =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=

@restricted
async def escrever_recado(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # inicia a conversa
    await update.message.reply_text("Escreva o seu recado no chat\n\n" "Envie /cancelar para cancelar esta ação\n" "⚠️ Atenção\! Você enviará recados para *todos* os canais registrados\! ⚠️", parse_mode= constants.ParseMode.MARKDOWN_V2)
    return MENSAGEM

async def assinatura(update: Update, context: ContextTypes.DEFAULT_TYPE, recado=recado):
    # guarda os valores da mensagem
    usuario = update.message.from_user
    logger.info(f"Mensagem de {usuario.first_name}: {update.message.text}")
    recado.update({'conteudo':update.message.text})

    await update.message.reply_text("Gostaria de assinar o recado?\n\n" "*SIM*: envie o seu nome\n" "*NÃO*: envie /pular para o reacado ser enviado em nome da direção do IFC câmpus Brusque", parse_mode= constants.ParseMode.MARKDOWN_V2)
    return ASSINATURA

async def skip(update: Update, context:ContextTypes.DEFAULT_TYPE, recado=recado):
    # comando de pular os dados de preenchimento da assinatura e envia o recado
    usuario = update.message.from_user
    logger.info(f"Assinatura de {usuario.first_name}: Att. a direção")

    await update.message.reply_text("Tudo feito! O recado será enviado logo logo :)")

    msg = f"{recado['titulo']}\n\n{recado['conteudo']}\n{recado['assinatura']}"
    for canal in CANAIS_CADASTRADOS:
        # envio do recado
        await context.bot.send_message(chat_id=canal, text=msg)
    return ConversationHandler.END

async def enviar_recado(update: Update, context: ContextTypes.DEFAULT_TYPE, recado=recado):
    # guarda os valores da assinatura e envia o recado
    usuario = update.message.from_user
    logger.info(f'Assinatura de {usuario.first_name}: {update.message.text}')
    recado.update({'assinatura':f'Att. {update.message.text}'})

    await update.message.reply_text("Tudo feito! O recado será enviado logo logo :)")

    msg = f"{recado['titulo']}\n\n{recado['conteudo']}\n{recado['assinatura']}"
    for canal in CANAIS_CADASTRADOS:
        # envio do recado
        await context.bot.send_message(chat_id=canal, text=msg)
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # cancelamento do comando
    usuario = update.message.from_user
    logger.info(f"{usuario.first_name} cancelou o comando RECADO")

    await update.message.reply_text("Ação cancelada...")
    return ConversationHandler.END

# =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=

async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # resposta ao receber um comando não identificado
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Desculpe, não tenho um comando assim :(")

if __name__ == '__main__':
    application = ApplicationBuilder().token(getenv('TOKEN')).build()
    
    # criando comandos
    start_handler = CommandHandler('start', start)
    registar_canal_handler = CommandHandler('registrar_canal', registrar_canal)
    ver_id_handler = CommandHandler('ver_id', ver_id)
    ver_horario_handler = CommandHandler('ver_horario', ver_horario)
    recado_handler = ConversationHandler(
        entry_points = [CommandHandler('escrever_recado', escrever_recado)],
        states= {
            MENSAGEM: [MessageHandler(filters.TEXT, assinatura)],
            ASSINATURA: [MessageHandler(filters.TEXT, enviar_recado), CommandHandler("pular", skip)]
        },
        fallbacks = [CommandHandler("cancelar", cancel)]
    )
    no_command_handler = MessageHandler(filters.COMMAND, unknown)

    # add comandos ao app
    application.add_handler(start_handler)
    application.add_handler(registar_canal_handler)
    application.add_handler(ver_id_handler)
    application.add_handler(ver_horario_handler)
    application.add_handler(recado_handler)
    application.add_handler(no_command_handler)
    
    application.run_polling()