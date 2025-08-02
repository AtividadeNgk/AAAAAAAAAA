import modules.manager as manager
import json

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, CallbackContext, CallbackQueryHandler, ContextTypes, ConversationHandler, MessageHandler, filters

from modules.utils import process_command, is_admin, cancel, error_callback

# Estados da conversa
GATILHO_MENU, GATILHO_TIPO, GATILHO_TEXTO, GATILHO_GERENCIAR = range(4)

async def gatilhos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    command_check = await process_command(update, context)
    if not command_check:
        return ConversationHandler.END
    
    if not await is_admin(context, update.message.from_user.id):
        return ConversationHandler.END
    
    context.user_data['conv_state'] = "gatilhos"
    
    # Pega gatilhos configurados
    gatilhos_config = manager.get_bot_gatilhos(context.bot_data['id'])
    
    # Monta o teclado
    keyboard = []
    
    # Ver Ofertas
    if gatilhos_config.get('ver_ofertas'):
        keyboard.append([InlineKeyboardButton("🎯 Ver Ofertas ✅", callback_data="gatilho_gerenciar_ver_ofertas")])
    else:
        keyboard.append([InlineKeyboardButton("🎯 Ver Ofertas", callback_data="gatilho_config_ver_ofertas")])
    
    # Escolher Plano
    if gatilhos_config.get('escolher_plano'):
        keyboard.append([InlineKeyboardButton("📋 Escolher Plano ✅", callback_data="gatilho_gerenciar_escolher_plano")])
    else:
        keyboard.append([InlineKeyboardButton("📋 Escolher Plano", callback_data="gatilho_config_escolher_plano")])
    
    # Gerar PIX
    if gatilhos_config.get('gerar_pix'):
        keyboard.append([InlineKeyboardButton("💳 Gerar PIX ✅", callback_data="gatilho_gerenciar_gerar_pix")])
    else:
        keyboard.append([InlineKeyboardButton("💳 Gerar PIX", callback_data="gatilho_config_gerar_pix")])
    
    keyboard.append([InlineKeyboardButton("❌ Cancelar", callback_data="cancelar")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "🧠 𝗚𝗮𝘁𝗶𝗹𝗵𝗼𝘀 𝗠𝗲𝗻𝘁𝗮𝗶𝘀\n\n"
        "Configure notificações estratégicas para aumentar suas conversões.",
        reply_markup=reply_markup
    )
    
    return GATILHO_MENU

async def gatilho_menu_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    
    if query.data == 'cancelar':
        await cancel(update, context)
        return ConversationHandler.END
    
    # Se é para gerenciar (já existe)
    if query.data.startswith('gatilho_gerenciar_'):
        local = query.data.replace('gatilho_gerenciar_', '')
        context.user_data['gatilho_local'] = local
        
        # Pega a configuração atual
        gatilhos_config = manager.get_bot_gatilhos(context.bot_data['id'])
        gatilho = gatilhos_config.get(local, {})
        
        tipo_texto = "Popup Central" if gatilho.get('tipo') == 'popup' else "Popup Topo"
        
        keyboard = [
            [InlineKeyboardButton("🗑 Deletar", callback_data="gatilho_deletar")],
            [InlineKeyboardButton("❌ Voltar", callback_data="gatilho_voltar")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.message.edit_text(
            f"⚙️ 𝗚𝗮𝘁𝗶𝗹𝗵𝗼 𝗖𝗼𝗻𝗳𝗶𝗴𝘂𝗿𝗮𝗱𝗼\n\n"
            f"📍 Local: {local.replace('_', ' ').title()}\n"
            f"🎯 Tipo: {tipo_texto}\n"
            f"💬 Mensagem: {gatilho.get('texto', 'Sem texto')}\n",
            reply_markup=reply_markup
        )
        return GATILHO_GERENCIAR
    
    # Se é para configurar novo
    elif query.data.startswith('gatilho_config_'):
        local = query.data.replace('gatilho_config_', '')
        context.user_data['gatilho_local'] = local
        
        keyboard = [
            [InlineKeyboardButton("🔔 Popup Central", callback_data="tipo_popup")],
            [InlineKeyboardButton("📍 Popup Topo", callback_data="tipo_topo")],
            [InlineKeyboardButton("❌ Cancelar", callback_data="cancelar")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.message.edit_text(
            "Qual estilo de pop-up você deseja?",
            reply_markup=reply_markup
        )
        return GATILHO_TIPO

async def gatilho_tipo_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    
    if query.data == 'cancelar':
        await cancel(update, context)
        return ConversationHandler.END
    
    # Salva o tipo escolhido
    tipo = 'popup' if query.data == 'tipo_popup' else 'topo'
    context.user_data['gatilho_tipo'] = tipo
    
    keyboard = [[InlineKeyboardButton("❌ Cancelar", callback_data="cancelar")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.message.edit_text(
        "📝 Digite o texto do gatilho:\n"
        "(máximo 200 caracteres)\n\n"
        "Exemplo: 🔥 23 pessoas compraram hoje!",
        reply_markup=reply_markup
    )
    
    return GATILHO_TEXTO

async def gatilho_receber_texto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = update.message.text.strip()
    
    # Validações
    if len(texto) > 200:
        await update.message.reply_text("⚠️ Texto muito longo! Máximo 200 caracteres.")
        return GATILHO_TEXTO
    
    if len(texto) < 5:
        await update.message.reply_text("⚠️ Texto muito curto! Mínimo 5 caracteres.")
        return GATILHO_TEXTO
    
    # Salva o gatilho
    local = context.user_data['gatilho_local']
    tipo = context.user_data['gatilho_tipo']
    
    # Pega gatilhos atuais
    gatilhos_config = manager.get_bot_gatilhos(context.bot_data['id'])
    
    # Adiciona/atualiza o novo
    gatilhos_config[local] = {
        'tipo': tipo,
        'texto': texto
    }
    
    # Salva no banco
    manager.update_bot_gatilhos(context.bot_data['id'], gatilhos_config)
    
    tipo_texto = "Popup Central" if tipo == 'popup' else "Popup Topo"
    
    await update.message.reply_text(
        f"✅ 𝗚𝗮𝘁𝗶𝗹𝗵𝗼 𝗰𝗼𝗻𝗳𝗶𝗴𝘂𝗿𝗮𝗱𝗼 𝗰𝗼𝗺 𝘀𝘂𝗰𝗲𝘀𝘀𝗼!\n\n"
        f"📍 Local: {local.replace('_', ' ').title()}\n"
        f"🎯 Tipo: {tipo_texto}\n"
        f"💬 Mensagem: {texto}"
    )
    
    context.user_data['conv_state'] = False
    return ConversationHandler.END

async def gatilho_gerenciar_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    
    if query.data == 'gatilho_voltar':
        # Volta para o menu inicial
        return await gatilhos(update, context)
    
    elif query.data == 'gatilho_deletar':
        local = context.user_data['gatilho_local']
        
        # Pega gatilhos atuais
        gatilhos_config = manager.get_bot_gatilhos(context.bot_data['id'])
        
        # Remove o gatilho
        if local in gatilhos_config:
            del gatilhos_config[local]
        
        # Salva no banco
        manager.update_bot_gatilhos(context.bot_data['id'], gatilhos_config)
        
        await query.message.edit_text(
            f"✅ Gatilho removido com sucesso!"
        )
        
        context.user_data['conv_state'] = False
        return ConversationHandler.END

# ConversationHandler
conv_handler_gatilhos = ConversationHandler(
    entry_points=[CommandHandler("gatilhos", gatilhos)],
    states={
        GATILHO_MENU: [CallbackQueryHandler(gatilho_menu_callback)],
        GATILHO_TIPO: [CallbackQueryHandler(gatilho_tipo_callback)],
        GATILHO_TEXTO: [MessageHandler(~filters.COMMAND, gatilho_receber_texto), CallbackQueryHandler(cancel)],
        GATILHO_GERENCIAR: [CallbackQueryHandler(gatilho_gerenciar_callback)]
    },
    fallbacks=[CallbackQueryHandler(error_callback)]
)