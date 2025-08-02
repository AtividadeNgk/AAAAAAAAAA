import modules.manager as manager
import modules.payment as payment
import json, re, requests

config = json.loads(open('./config.json', 'r').read())

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Application, CommandHandler, CallbackContext, CallbackQueryHandler, ContextTypes, ConversationHandler, MessageHandler, filters, Updater, CallbackContext, ChatJoinRequestHandler
from telegram.error import BadRequest, Conflict

from modules.utils import process_command, is_admin, error_callback, error_message, cancel, escape_markdown_v2

GATEWAY_RECEBER, GATEWAY_ESCOLHA = range(2)

#comando adeus
async def gateway(update: Update, context: ContextTypes.DEFAULT_TYPE):
    command_check = await process_command(update, context)
    planos = manager.get_bot_plans(context.bot_data['id'])
    if not command_check:
        return ConversationHandler.END
    if not await is_admin(context, update.message.from_user.id):
        
        return ConversationHandler.END
    context.user_data['conv_state'] = "gateway"

    keyboard = [
            [InlineKeyboardButton("Mercado Pago", callback_data="mp"), InlineKeyboardButton("Pushinpay", callback_data="push")],
            [InlineKeyboardButton("❌ CANCELAR", callback_data="cancelar")]]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "🔐 Qual gateway deseja adicionar?\n\n"
        ">𝗖𝗼𝗺𝗼 𝗳𝘂𝗻𝗰𝗶𝗼𝗻𝗮\\? Conecte seu bot com Mercado Pago ou PushinPay para processar pagamentos\\.",
        reply_markup=reply_markup,
        parse_mode='MarkdownV2'
    )
    return GATEWAY_ESCOLHA

async def gateway_escolha(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    if query.data == 'cancelar':
        await cancel(update, context)
        return ConversationHandler.END
    elif query.data == 'mp':
        # Constrói a URL
        mp_url = f"https://auth.mercadopago.com/authorization?client_id={config['client_id']}&response_type=code&platform_id=mp&state={context.bot_data['id']}&redirect_url={config['url']}/callback"
        
        # Cria o botão com o link
        keyboard = [[InlineKeyboardButton("🔗 Conectar Mercado Pago", url=mp_url)]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.message.edit_text(
            "🔒 Clique no botão abaixo para vincular seu Mercado Pago.", 
            reply_markup=reply_markup
        )
        
        context.user_data['conv_state'] = False
        return ConversationHandler.END
    elif query.data == 'push':
        keyboard = [[InlineKeyboardButton("❌ CANCELAR", callback_data="cancelar")]]
        reply_markup = InlineKeyboardMarkup(keyboard)        
        await query.message.edit_text("🔒 Envie o token da PushinPay.", reply_markup=reply_markup)
        return GATEWAY_RECEBER
    
async def recebe_gateway(update: Update, context: ContextTypes.DEFAULT_TYPE):
    token_recebido = update.message.text.strip()
    keyboard = [[InlineKeyboardButton("❌ CANCELAR", callback_data="cancelar")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    if not update.message.text:
        await update.message.reply_text(text=f"⛔ Token invalido, por favor envie um valido")
        return GATEWAY_RECEBER
    if not payment.verificar_push(token_recebido):
        await update.message.reply_text(
            "❌ Token inválido\\! O Token deve ser nesse formato ⬋\n\n"
            ">36498\\|kMLGkibg5Z2D1Ap8hyvabkYsf5emCcREMpRMkTPa2c802374",
            reply_markup=reply_markup,
            parse_mode='MarkdownV2'
        )
        return GATEWAY_RECEBER
    
    manager.update_bot_gateway(context.bot_data['id'], {'type':'pp', 'token':token_recebido})
    await update.message.reply_text(text=f"✅ Gateway modificado com sucesso")
    context.user_data['conv_state'] = False
    return ConversationHandler.END

conv_handler_gateway = ConversationHandler(
    entry_points=[CommandHandler("gateway", gateway)],
    states={
        GATEWAY_ESCOLHA: [CallbackQueryHandler(gateway_escolha)],
        GATEWAY_RECEBER: [MessageHandler(~filters.COMMAND, recebe_gateway), CallbackQueryHandler(cancel)]
    },
    fallbacks=[CallbackQueryHandler(error_callback)]
    )
