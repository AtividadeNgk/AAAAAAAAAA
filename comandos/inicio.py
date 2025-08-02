import modules.manager as manager
import json, re, requests


from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Application, CommandHandler, CallbackContext, CallbackQueryHandler, ContextTypes, ConversationHandler, MessageHandler, filters, Updater, CallbackContext, ChatJoinRequestHandler
from telegram.error import BadRequest, Conflict

from modules.utils import process_command, is_admin, cancel, error_callback, error_message

keyboardc = [
            [InlineKeyboardButton("❌ Cancelar", callback_data="cancelar")]
        ]
cancel_markup = InlineKeyboardMarkup(keyboardc)


INICIO_ESCOLHA, INICIO_ADICIONAR_OU_DELETAR, INICIO_RECEBER = range(3)


# Comando definir inicio
# /Inicio
async def inicio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    command_check = await process_command(update, context)
    if not command_check:
        return ConversationHandler.END

    if not await is_admin(context, update.message.from_user.id):
        return ConversationHandler.END
    
    context.user_data['inicio_context'] = manager.get_bot_config(context.bot_data['id'])
    context.user_data['conv_state'] = "inicio"

    keyboard = [
        [InlineKeyboardButton("Midia Inicial", callback_data="midia"), InlineKeyboardButton("Texto 1", callback_data="texto1")],
        [InlineKeyboardButton("Texto 2", callback_data="texto2"), InlineKeyboardButton("Botão", callback_data="botao")],
        [InlineKeyboardButton("❌ Cancelar", callback_data="cancelar")]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "📱 O que deseja modificar no início?\n\n"
        ">𝗖𝗼𝗺𝗼 𝗳𝘂𝗻𝗰𝗶𝗼𝗻𝗮\\? Esse comando serve para personalizar o início do seu bot\\. Personalize textos, midia inicial e o botão inicial\\.",
        reply_markup=reply_markup,
        parse_mode='MarkdownV2'
    )
    return INICIO_ESCOLHA

async def inicio_escolha(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()

    if query.data == 'cancelar':
        await cancel(update, context)
        return ConversationHandler.END

    context.user_data['inicio_acao'] = query.data

    # Se for botão, vai direto para receber o texto
    if query.data == 'botao':
        keyboard = [[InlineKeyboardButton("❌ Cancelar", callback_data="cancelar")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.edit_text(
            "🕹 Envie abaixo o texto que deseja para o botão inicial\n\n"
            ">𝗖𝗼𝗺𝗼 𝗳𝘂𝗻𝗰𝗶𝗼𝗻𝗮\\? Esse texto é aplicado no botão que o usuário clica para exibir a lista de planos no início do bot\\.",
            reply_markup=reply_markup,
            parse_mode='MarkdownV2'
        )
        return INICIO_RECEBER

    keyboard = [
        [InlineKeyboardButton("🟢 Adicionar", callback_data="adicionar"), InlineKeyboardButton("🧹 Remover", callback_data="deletar")],
        [InlineKeyboardButton("❌ Cancelar", callback_data="cancelar")]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    # Textos específicos para cada opção
    if query.data == 'midia':
        texto = "🎬 O que deseja fazer com a mídia inicial?"
    elif query.data == 'texto1':
        texto = "📝 O que deseja fazer com o Texto 1?"
    elif query.data == 'texto2':
        texto = "📝 O que deseja fazer com o Texto 2?"
    else:
        texto = f"🛠️ Deseja adicionar ou deletar o valor para {query.data}?"
    
    await query.message.edit_text(texto, reply_markup=reply_markup)
    return INICIO_ADICIONAR_OU_DELETAR

async def inicio_adicionar_ou_deletar(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()

    acao = context.user_data.get('inicio_acao')
    if query.data == 'cancelar':
        await cancel(update, context)
        return ConversationHandler.END

    if query.data == 'deletar':
        # Verifica se o texto já foi definido
        if acao == 'texto2' and not context.user_data['inicio_context'].get('texto2'):
            await query.message.edit_text("❌ Não é possível deletar o Texto 2, pois o mesmo ainda não foi definido.")
            context.user_data['conv_state'] = False
            return ConversationHandler.END
            
        if acao == 'texto1' and not context.user_data['inicio_context'].get('texto1'):
            await query.message.edit_text("❌ Não é possível deletar o Texto 1, pois o mesmo ainda não foi definido.")
            context.user_data['conv_state'] = False
            return ConversationHandler.END

        context.user_data['inicio_context'][acao] = False
        
        # Mensagens personalizadas para remoção
        if acao == 'midia':
            await query.message.edit_text("✅ Mídia inicial removida com sucesso.")
        elif acao == 'texto1':
            await query.message.edit_text("✅ Texto 1 foi removido com sucesso.")
        elif acao == 'texto2':
            await query.message.edit_text("✅ Texto 2 foi removido com sucesso.")
        else:
            await query.message.edit_text(f"✅ {acao.capitalize()} foi deletado com sucesso.")
            
        manager.update_bot_config(context.bot_data['id'], context.user_data['inicio_context'])
        
        context.user_data['conv_state'] = False
        return ConversationHandler.END

    elif query.data == 'adicionar':
        keyboard = [[InlineKeyboardButton("❌ Cancelar", callback_data="cancelar")]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        if acao == "midia":
            await query.message.edit_text(
                "🎬 Envie abaixo a mídia inicial que deseja definir ⬋\n\n"
                ">𝗖𝗼𝗺𝗼 𝗳𝘂𝗻𝗰𝗶𝗼𝗻𝗮\\? A mídia enviada será aplicada no início do seu bot\\.",
                reply_markup=reply_markup,
                parse_mode='MarkdownV2'
            )
        elif acao == "texto1":
            await query.message.edit_text("📝 Envie o Texto 1.", reply_markup=reply_markup)
        elif acao == "texto2":
            await query.message.edit_text("📝 Envie o Texto 2.", reply_markup=reply_markup)
        return INICIO_RECEBER

async def inicio_receber(update: Update, context: ContextTypes.DEFAULT_TYPE):
    acao = context.user_data.get('inicio_acao')
    for i in range(10):
        print('receber')
    mensagem = update.message.text if update.message else None
    try:
        if acao == "midia":
            if update.message.photo or update.message.video:
                try:
                    media_file = await (update.message.photo[-1] if update.message.photo else update.message.video).get_file()
                    context.user_data['inicio_context']['midia'] = {
                        'file': media_file.file_id,
                        'type': 'photo' if update.message.photo else 'video'
                    }
                    await update.message.reply_text("✅ Mídia inicial atualizada com sucesso.")
                    manager.update_bot_config(context.bot_data['id'], context.user_data['inicio_context'])
                except Exception as media_error:
                    if "File is too big" in str(media_error) or "file is too big" in str(media_error).lower():
                        await update.message.reply_text(
                            "❌ O Telegram limita mídias a 20MB para bots\\. Por favor, envie uma menor\\.\n\n"
                            ">𝗗𝗶𝗰𝗮\\: Bots do Telegram só aceitam mídias de até 20MB\\. Use um compressor de vídeos online para reduzir o tamanho da sua mídia\\.",
                            reply_markup=cancel_markup,
                            parse_mode='MarkdownV2'
                        )
                        return INICIO_RECEBER
                    else:
                        raise media_error
            else:
                for i in range(10):
                    print('erro')
                await update.message.reply_text("⛔️ Por favor, envie apenas mídia.", reply_markup=cancel_markup)
                return INICIO_RECEBER

        elif acao in ["texto1", "texto2"]:
            # Verifica se é texto puro (não é mídia, sticker, documento, áudio, etc)
            if not update.message.text or update.message.photo or update.message.video or update.message.sticker or update.message.document or update.message.audio or update.message.voice or update.message.video_note or update.message.animation:
                await update.message.reply_text("⛔ Por favor, envie apenas texto.", reply_markup=cancel_markup)
                return INICIO_RECEBER
            context.user_data['inicio_context'][acao] = mensagem
            if acao == "texto1":
                await update.message.reply_text("✅ Texto 1 atualizado com sucesso.")
            else:
                await update.message.reply_text("✅ Texto 2 atualizado com sucesso.")
            manager.update_bot_config(context.bot_data['id'], context.user_data['inicio_context'])
            
        elif acao == "botao":
            # Verifica se é texto puro (não é mídia, sticker, documento, áudio, etc)
            if not update.message.text or update.message.photo or update.message.video or update.message.sticker or update.message.document or update.message.audio or update.message.voice or update.message.video_note or update.message.animation:
                await update.message.reply_text("⛔ Por favor, envie apenas texto.", reply_markup=cancel_markup)
                return INICIO_RECEBER
            context.user_data['inicio_context']['button'] = mensagem
            await update.message.reply_text("✅ Texto do botão inicial atualizado com sucesso.")
            manager.update_bot_config(context.bot_data['id'], context.user_data['inicio_context'])

    except Exception as e:
        print('erro')
        await update.message.reply_text(f"⛔ Erro ao modificar o inicio: {str(e)}")
        context.user_data['conv_state'] = False
        return ConversationHandler.END

    context.user_data['conv_state'] = False
    return ConversationHandler.END


conv_handler_inicio = ConversationHandler(
    entry_points=[CommandHandler("inicio", inicio)],
    states={
        INICIO_ESCOLHA: [CallbackQueryHandler(inicio_escolha)],
        INICIO_ADICIONAR_OU_DELETAR: [CallbackQueryHandler(inicio_adicionar_ou_deletar)],
        INICIO_RECEBER: [MessageHandler(filters.ALL, inicio_receber)]
    },
    fallbacks=[CallbackQueryHandler(cancel)],
)
