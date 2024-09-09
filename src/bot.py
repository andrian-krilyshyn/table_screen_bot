import fitz  # PyMuPDF
import io
from googleapiclient.discovery import build
from google.oauth2 import service_account
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from telegram import Bot, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackContext, ContextTypes, CallbackQueryHandler
from datetime import datetime

# Ваш токен бота та ID чату
TOKEN = '7320369617:AAGitENCsLTIjqL9bPU-P7gJyC0fgSStz2U'
CHAT_ID = '-1002421170446'

# Налаштування для Google Sheets
SERVICE_ACCOUNT_FILE = 's.json'
SCOPES = ['https://www.googleapis.com/auth/drive']
SHEET_ID = '1_8vNN53eZMHwQ9w3mZySs0560cbpl-kX8MoUc94eNR8'

# Налаштування Google Drive API
credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES)
service = build('drive', 'v3', credentials=credentials)

# Завантаження PDF з Google Sheets
async def fetch_pdf():
    request = service.files().export_media(fileId=SHEET_ID, mimeType='application/pdf')
    fh = io.BytesIO(request.execute())
    with open('output.pdf', 'wb') as f:
        f.write(fh.getvalue())

# Збереження лише першої сторінки PDF
def save_first_page(input_pdf_path, output_pdf_path):
    doc = fitz.open(input_pdf_path)  # Відкриваємо PDF
    new_doc = fitz.open()  # Створюємо новий PDF документ
    new_doc.insert_pdf(doc, from_page=0, to_page=0)  # Копіюємо лише першу сторінку
    new_doc.save(output_pdf_path)  # Зберігаємо новий PDF з першою сторінкою
    new_doc.close()
    doc.close()

# Надсилання PDF у чат
async def send_pdf(pdf_path):
    bot = Bot(token=TOKEN)
    with open(pdf_path, 'rb') as pdf_file:
        sent_message = await bot.send_document(chat_id=CHAT_ID, document=pdf_file)
        table_name = "CO PEDRO DANIL"  # Змініть на відповідне джерело назви таблиці, якщо потрібно
    # Час надсилання
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # Надсилаємо текстове повідомлення як відповідь на надісланий PDF
    if sent_message:
        await bot.send_message(chat_id=CHAT_ID, text=f"Документ '{table_name}' был послан в {current_time}.", reply_to_message_id=sent_message.message_id)
    else:
        await bot.send_message(chat_id=CHAT_ID, text=f"Документ '{table_name}' был послан в {current_time}.")

# Основна робота: завантаження та надсилання PDF
async def job():
    await fetch_pdf()  # Завантажуємо PDF з Google Sheets
    save_first_page('output.pdf', 'CO_PEDRO_DANIL.pdf')  # Зберігаємо лише першу сторінку
    await send_pdf('CO_PEDRO_DANIL.pdf')  # Відправляємо першу сторінку як PDF

# Відповідь на команду /start
async def start(update: Update, context: CallbackContext):
    keyboard = [[InlineKeyboardButton("Выполнить действия", callback_data='run_job')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('Нажмите кнопку для выполнения действий.', reply_markup=reply_markup)

# Обробка натискання кнопки
async def button(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    if query.data == 'run_job':
        await job()

# Основна функція для запуску бота
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler('start', start))
    app.add_handler(CallbackQueryHandler(button))

    # Запуск асинхронного циклу планувальника
    scheduler = AsyncIOScheduler()
    scheduler.add_job(job, 'interval', minutes=30)  # Запуск кожні 30 хвилин
    scheduler.start()

    app.run_polling()

if __name__ == '__main__':
    main()
