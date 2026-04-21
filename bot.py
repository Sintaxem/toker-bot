import os
import json
import asyncio
import logging
import random
import google.generativeai as genai
from datetime import datetime, time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, filters
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GEMINI_KEY = os.environ.get("GEMINI_API_KEY")
OWNER_CHAT_ID = os.environ.get("OWNER_CHAT_ID")

genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

SINTAXEM_CONTEXT = """
Eres TOKER, el agente de contenido oficial de SINTAXEM — estudio de artes gráficas de Lucas Burone.
SINTAXEM se especializa en:
- Rotulación de vehículos (furgonetas, coches, flotas)
- Vinilos decorativos (hogar, cocinas, baños, muebles)
- Cartelería y señalética profesional
- Diseño gráfico

Zonas: Barcelona, Tarragona y Baleares
WhatsApp: +34 629 170 153
Email: info@sintaxem.com
Web: sintaxem.com
Instagram: @sintaxem (próximamente activo)
TikTok: @sintaxem (próximamente activo)

Lucas es diseñador gráfico y técnico industrial con taller propio. 
Su fuerte es la colocación profesional — él mismo instala todo.
Tono: cercano, profesional, con personalidad mediterránea.
"""

SERVICES = [
    "Rotulación de vehículos",
    "Vinilos decorativos hogar",
    "Cartelería y señalética",
    "Vinilos cocinas/baños",
    "Diseño gráfico",
    "Vinilos para oficinas"
]

POST_TYPES = [
    "Mostrar trabajo realizado",
    "Promoción especial",
    "Tips y consejos",
    "Antes y después",
    "Presentación de servicio"
]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome = (
        "👋 ¡Hola! Soy *TOKER*, tu agente de contenido de SINTAXEM.\n\n"
        "Puedo ayudarte con:\n"
        "📸 /post — Generar un post para Instagram\n"
        "🎬 /reel — Ideas para Reels/TikTok\n"
        "📅 /semana — Plan de contenido semanal\n"
        "💡 /idea — Inspiración de contenido\n"
        "📊 /stats — Ver historial de posts\n\n"
        "O simplemente escríbeme lo que necesitás 💬"
    )
    await update.message.reply_text(welcome, parse_mode='Markdown')

async def generate_post(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton(s, callback_data=f"serv_{i}")]
        for i, s in enumerate(SERVICES)
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "¿Qué servicio querés destacar hoy?",
        reply_markup=reply_markup
    )

async def generate_reel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = await update.message.reply_text("🎬 Generando idea de reel...")
    
    prompt = f"""{SINTAXEM_CONTEXT}
    
Genera una idea detallada de Reel para Instagram/TikTok de 15-30 segundos.
El reel debe ser sobre el proceso de instalación de vinilos o rotulación.

Formato JSON:
{{
    "titulo": "Título gancho del reel (máx 8 palabras)",
    "concepto": "Descripción del concepto visual (3-4 frases)",
    "estructura": [
        "0-3s: ...",
        "3-10s: ...", 
        "10-20s: ...",
        "20-30s: ..."
    ],
    "musica": "Tipo de música sugerida y mood",
    "caption": "Caption completo con emojis y hashtags",
    "plataforma_video": "CapCut (gratis) — descripción de cómo editarlo"
}}"""

    try:
        response = model.generate_content(f"{SINTAXEM}\n\n{prompt}")
        raw = response.text
        clean = raw.replace("```json", "").replace("```", "").strip()
        data = json.loads(clean)
        
        text = (
            f"🎬 *{data['titulo']}*\n\n"
            f"📋 *Concepto:*\n{data['concepto']}\n\n"
            f"🎞️ *Estructura:*\n" + "\n".join(f"  {s}" for s in data['estructura']) + "\n\n"
            f"🎵 *Música:* {data['musica']}\n\n"
            f"📝 *Caption:*\n{data['caption']}\n\n"
            f"✂️ *Edición:* {data['plataforma_video']}"
        )
        
        keyboard = [[
            InlineKeyboardButton("🔄 Otra idea", callback_data="reel_new"),
            InlineKeyboardButton("💾 Guardar", callback_data="reel_save")
        ]]
        await msg.edit_text(text, parse_mode='Markdown',
                           reply_markup=InlineKeyboardMarkup(keyboard))
    except Exception as e:
        await msg.edit_text(f"❌ Error: {str(e)}")

async def weekly_plan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = await update.message.reply_text("📅 Generando plan semanal...")
    
    prompt = f"""{SINTAXEM_CONTEXT}

Genera un plan de contenido para 7 días para Instagram y TikTok de SINTAXEM.
Varía los servicios, tipos de post y formatos.

Formato JSON con array de 7 días:
{{
    "semana": "Semana del {datetime.now().strftime('%d/%m/%Y')}",
    "dias": [
        {{
            "dia": "Lunes",
            "formato": "Post/Reel/Story",
            "servicio": "...",
            "tema": "...",
            "hora": "HH:MM",
            "caption_corto": "..."
        }}
    ]
}}"""

    try:
        response = model.generate_content(f"{SINTAXEM}\n\n{prompt}")
        raw = response.text
        clean = raw.replace("```json", "").replace("```", "").strip()
        data = json.loads(clean)
        
        text = f"📅 *Plan de Contenido — {data['semana']}*\n\n"
        for dia in data['dias']:
            emoji = "📸" if dia['formato'] == "Post" else "🎬" if dia['formato'] == "Reel" else "📱"
            text += (
                f"{emoji} *{dia['dia']}* — {dia['hora']}\n"
                f"  _{dia['formato']}_ • {dia['servicio']}\n"
                f"  {dia['tema']}\n\n"
            )
        
        await msg.edit_text(text, parse_mode='Markdown')
    except Exception as e:
        await msg.edit_text(f"❌ Error: {str(e)}")

async def inspiration(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = await update.message.reply_text("💡 Buscando inspiración...")
    
    prompt = f"""{SINTAXEM_CONTEXT}

Dame 5 ideas creativas de contenido viral para SINTAXEM.
Que sean originales, divertidas y reales — basadas en el día a día de un instalador de vinilos.
Incluye situaciones graciosas, behind the scenes, tips útiles.

Formato: lista numerada con emoji, título y descripción breve."""

    try:
        response = model.generate_content(f"{SINTAXEM}\n\n{prompt}")
        text = f"💡 *Ideas de Contenido para SINTAXEM*\n\n{response.text}"
        await msg.edit_text(text, parse_mode='Markdown')
    except Exception as e:
        await msg.edit_text(f"❌ Error: {str(e)}")

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    
    if data.startswith("serv_"):
        idx = int(data.split("_")[1])
        service = SERVICES[idx]
        context.user_data['service'] = service
        
        keyboard = [
            [InlineKeyboardButton(t, callback_data=f"type_{i}")]
            for i, t in enumerate(POST_TYPES)
        ]
        await query.edit_message_text(
            f"Servicio: *{service}*\n\n¿Qué tipo de post?",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    elif data.startswith("type_"):
        idx = int(data.split("_")[1])
        post_type = POST_TYPES[idx]
        service = context.user_data.get('service', 'vinilos')
        
        await query.edit_message_text("✍️ Generando tu post...")
        
        prompt = f"""{SINTAXEM_CONTEXT}

Genera un post completo para Instagram sobre:
- Servicio: {service}
- Tipo: {post_type}
- Fecha: {datetime.now().strftime('%A %d de %B')}

Formato JSON:
{{
    "ig_caption": "Caption completo con emojis, historia, CTA y teléfono",
    "ig_hashtags": "28 hashtags relevantes en español e inglés",
    "mejor_hora": "Hora ideal de publicación hoy",
    "idea_visual": "Qué foto o video usar"
}}"""

        try:
            response = model.generate_content(f"{SINTAXEM}\n\n{prompt}")
            raw = response.text
            clean = raw.replace("```json", "").replace("```", "").strip()
            post_data = json.loads(clean)
            
            text = (
                f"✅ *Post generado — {service}*\n\n"
                f"🕐 Publicar a las: *{post_data['mejor_hora']}*\n"
                f"📸 Visual: _{post_data['idea_visual']}_\n\n"
                f"📝 *Caption:*\n{post_data['ig_caption']}\n\n"
                f"#️⃣ *Hashtags:*\n{post_data['ig_hashtags']}"
            )
            
            keyboard = [[
                InlineKeyboardButton("🔄 Regenerar", callback_data=f"type_{idx}"),
                InlineKeyboardButton("📤 Listo!", callback_data="post_done")
            ]]
            await query.edit_message_text(
                text, parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        except Exception as e:
            await query.edit_message_text(f"❌ Error: {str(e)}")
    
    elif data == "post_done":
        await query.edit_message_text(
            "✅ ¡Post listo para publicar!\n\n"
            "📋 Copiá el caption de arriba\n"
            "📸 Elegí la mejor foto del trabajo\n"
            "🚀 ¡Publicá en Instagram!\n\n"
            "Escribí /post para generar otro 👆"
        )
    
    elif data == "reel_new":
        await query.edit_message_text("🎬 Generando nueva idea...")
        fake_update = type('obj', (object,), {'message': query.message})()
        await generate_reel(fake_update, context)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    msg = await update.message.reply_text("⏳ Pensando...")
    
    prompt = f"""{SINTAXEM_CONTEXT}

El usuario (Lucas, dueño de SINTAXEM) te pregunta: "{user_text}"

Responde de forma útil, concreta y en español. 
Si pide contenido, generalo completo.
Si es una pregunta, respondela directamente.
Máximo 500 palabras."""

    try:
        response = model.generate_content(f"{SINTAXEM}\n\n{prompt}")
        await msg.edit_text(response.text, parse_mode='Markdown')
    except Exception as e:
        await msg.edit_text(f"❌ Error: {str(e)}")

async def daily_post_job(context: ContextTypes.DEFAULT_TYPE):
    if not OWNER_CHAT_ID:
        return
    
    import random
    service = random.choice(SERVICES)
    
    prompt = f"""{SINTAXEM_CONTEXT}

Post diario automático — {datetime.now().strftime('%A %d de %B de %Y')}
Servicio aleatorio del día: {service}

Genera el post más impactante posible para hoy.
JSON con ig_caption, ig_hashtags, idea_visual, mejor_hora."""

    try:
        response = model.generate_content(f"{SINTAXEM}\n\n{prompt}")
        raw = response.text
        clean = raw.replace("```json", "").replace("```", "").strip()
        data = json.loads(clean)
        
        text = (
            f"🌅 *Post del día — {datetime.now().strftime('%d/%m')}*\n\n"
            f"📸 Visual: _{data['idea_visual']}_\n"
            f"🕐 Publicar a: *{data['mejor_hora']}*\n\n"
            f"📝 *Caption:*\n{data['ig_caption']}\n\n"
            f"#️⃣ *Hashtags:*\n{data['ig_hashtags']}"
        )
        
        await context.bot.send_message(
            chat_id=OWNER_CHAT_ID,
            text=text,
            parse_mode='Markdown'
        )
    except Exception as e:
        logger.error(f"Error en post diario: {e}")

def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("post", generate_post))
    app.add_handler(CommandHandler("reel", generate_reel))
    app.add_handler(CommandHandler("semana", weekly_plan))
    app.add_handler(CommandHandler("idea", inspiration))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    job_queue = app.job_queue
    job_queue.run_daily(
        daily_post_job,
        time=time(10, 0, 0),
        name="daily_post"
    )
    
    logger.info("TOKER iniciado!")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
