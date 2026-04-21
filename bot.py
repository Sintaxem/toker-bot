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
model = genai.GenerativeModel("gemini-2.0-flash-exp")

SINTAXEM = """
Eres TOKER, el asistente personal y agente de contenido de SINTAXEM.
Eres el cerebro digital de Lucas Burone, CEO de SINTAXEM.

SOBRE SINTAXEM:
- Estudio de artes gráficas: vinilos, rotulación de vehículos, cartelería, diseño gráfico
- Zonas: Barcelona, Tarragona y Baleares
- Web: sintaxem.com | IG: @sintaxem
- WhatsApp: +34 629 170 153 | Email: info@sintaxem.com

PERSONALIDAD:
- Directo, claro, útil y con personalidad propia
- En español, tono cercano y profesional
- Conocés todo sobre SINTAXEM

CAPACIDADES:
- Generar posts, copies y hashtags para Instagram y TikTok
- Crear planes de contenido semanales
- Ideas creativas para reels y stories
- Responder preguntas sobre el negocio
"""

SERVICES = [
    "Rotulación de vehículos",
    "Vinilos decorativos para hogar",
    "Cartelería y señalética",
    "Vinilos para cocinas y baños",
    "Diseño gráfico y branding",
    "Vinilos para oficinas y locales"
]

async def ask_gemini(prompt: str) -> str:
    try:
        response = model.generate_content(f"{SINTAXEM}\n\n{prompt}")
        return response.text
    except Exception as e:
        logger.error(f"Gemini error: {e}")
        return f"Error al conectar con la IA: {str(e)}"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "👋 ¡Hola Lucas! Soy *TOKER*, tu agente de SINTAXEM.\n\n"
        "📸 /post — Post para Instagram\n"
        "🎬 /reel — Idea para Reel o TikTok\n"
        "📅 /semana — Plan de contenido semanal\n"
        "💡 /idea — Inspiración de contenido\n\n"
        "O escribime lo que necesitás 💬"
    )
    await update.message.reply_text(text, parse_mode='Markdown')

async def generate_post(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton(s, callback_data=f"post_{i}")] for i, s in enumerate(SERVICES)]
    await update.message.reply_text(
        "¿Qué servicio querés destacar?",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def generate_reel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = await update.message.reply_text("🎬 Generando idea de reel...")
    prompt = f"""Genera una idea creativa de Reel/TikTok de 15-30 segundos para SINTAXEM.
Debe mostrar el proceso de instalación de vinilos de forma visual y atractiva.

Responde con este formato:
🎬 **TÍTULO:** (hook de 6-8 palabras)
📋 **CONCEPTO:** (2-3 frases)
🎞️ **ESTRUCTURA:**
- 0-3s: ...
- 3-10s: ...
- 10-20s: ...
- 20-30s: ...
🎵 **MÚSICA:** (tipo y mood)
📝 **CAPTION:** (completo con hashtags)
✂️ **EDICIÓN:** (tips con CapCut gratis)"""

    response = await ask_gemini(prompt)
    keyboard = [[InlineKeyboardButton("🔄 Otra idea", callback_data="reel_new")]]
    await msg.edit_text(response, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard))

async def weekly_plan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = await update.message.reply_text("📅 Generando plan semanal...")
    prompt = f"""Crea un plan de contenido para los próximos 7 días para SINTAXEM.
Fecha inicio: {datetime.now().strftime('%d/%m/%Y')}
Varía servicios, formatos (Post/Reel/Story) y horarios.

📅 **PLAN SEMANAL SINTAXEM**

Para cada día incluye:
- Formato y hora
- Servicio a destacar
- Tema del contenido
- Caption corto"""

    response = await ask_gemini(prompt)
    await msg.edit_text(response, parse_mode='Markdown')

async def inspiration(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = await update.message.reply_text("💡 Buscando ideas...")
    prompt = """Dame 5 ideas originales y creativas de contenido para SINTAXEM.
Basadas en el día a día real de un instalador de vinilos en Barcelona.
Incluye situaciones divertidas, behind the scenes y tips útiles.
Que sean virales y auténticas. Formato con emoji y descripción de 2 líneas."""

    response = await ask_gemini(prompt)
    await msg.edit_text(f"💡 *Ideas de Contenido SINTAXEM*\n\n{response}", parse_mode='Markdown')

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data.startswith("post_"):
        idx = int(data.split("_")[1])
        service = SERVICES[idx]
        await query.edit_message_text(f"✍️ Generando post para *{service}*...", parse_mode='Markdown')

        prompt = f"""Genera un post completo para Instagram de SINTAXEM sobre: {service}
Fecha: {datetime.now().strftime('%A %d de %B de %Y')}

🕐 **MEJOR HORA:** (hora ideal hoy)
📸 **IDEA VISUAL:** (qué foto o video hacer)
📝 **CAPTION:** (completo con emojis, historia y CTA con +34 629 170 153)
#️⃣ **HASHTAGS:** (28-30 hashtags en español e inglés)"""

        response = await ask_gemini(prompt)
        keyboard = [[
            InlineKeyboardButton("🔄 Regenerar", callback_data=data),
            InlineKeyboardButton("✅ Listo!", callback_data="post_done")
        ]]
        await query.edit_message_text(response, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard))

    elif data == "post_done":
        await query.edit_message_text("✅ ¡Post listo! Copiá el caption, elegí la mejor foto y publicá en @sintaxem 🚀")

    elif data == "reel_new":
        await query.edit_message_text("🎬 Generando nueva idea...")
        prompt = """Genera otra idea diferente de Reel/TikTok para SINTAXEM. 
Que sea diferente a la anterior, más divertida y viral."""
        response = await ask_gemini(prompt)
        keyboard = [[InlineKeyboardButton("🔄 Otra idea", callback_data="reel_new")]]
        await query.edit_message_text(response, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard))

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    msg = await update.message.reply_text("⏳ Pensando...")

    prompt = f"""Lucas te pregunta o pide: "{user_text}"
Respondé de forma útil, concreta y directa.
Si pide contenido, generalo completo.
Si es una pregunta, respondela.
Máximo 400 palabras."""

    response = await ask_gemini(prompt)
    await msg.edit_text(response, parse_mode='Markdown')

async def daily_post_job(context: ContextTypes.DEFAULT_TYPE):
    if not OWNER_CHAT_ID:
        return
    service = random.choice(SERVICES)
    prompt = f"""Post diario automático SINTAXEM — {datetime.now().strftime('%A %d de %B de %Y')}
Servicio del día: {service}

🌅 POST DEL DÍA

Genera el post más impactante para hoy con:
- Mejor hora para publicar
- Idea visual
- Caption completo
- Hashtags"""

    try:
        response = await ask_gemini(prompt)
        await context.bot.send_message(
            chat_id=int(OWNER_CHAT_ID),
            text=f"🌅 *Post del día — {datetime.now().strftime('%d/%m')}*\n\n{response}",
            parse_mode='Markdown'
        )
    except Exception as e:
        logger.error(f"Error post diario: {e}")

def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("post", generate_post))
    app.add_handler(CommandHandler("reel", generate_reel))
    app.add_handler(CommandHandler("semana", weekly_plan))
    app.add_handler(CommandHandler("idea", inspiration))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    app.job_queue.run_daily(
        daily_post_job,
        time=time(10, 0, 0),
        name="daily_post"
    )

    logger.info("🤖 TOKER iniciado!")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
