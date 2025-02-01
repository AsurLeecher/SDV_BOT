import logging
import os
import requests
import itertools
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    CommandHandler,
    ConversationHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

# Constants
ROOT_DIR = os.getcwd()
DOWNLOAD_DIR = os.path.join(ROOT_DIR, "downloads")
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# Stages for ConversationHandler
AUTH_CODE, BATCH_ID, SUBJECT_IDS = range(3)

# Helper Functions
def get_batches(auth_code):
    """Fetch batches using the provided token."""
    headers = {
        'authorization': f"Bearer {auth_code}",
        'client-id': '5eb393ee95fab7468a79d189',
        'user-agent': 'Android',
    }
    result = ""
    try:
        for page in itertools.count(1):
            try:
                response = requests.get(
                    f'https://api.penpencil.xyz/v3/batches/my-batches?page={page}&mode=1',
                    headers=headers,
                    timeout=10,
                )
                response.raise_for_status()
            except requests.exceptions.RequestException as e:
                logging.error(f"Request failed: {e}")
                return None

            data = response.json().get("data", [])
            if not data:
                break
            for batch in data:
                batch_id = batch["_id"]
                name = batch["name"]
                price = batch.get("feeId", {}).get("total", "Free")
                result += f"𝑩𝒂𝒕𝒄𝒉 𝑰𝑫💡: ```{batch_id}```\n𝑩𝒂𝒕𝒄𝒉 𝑵𝒂𝒎𝒆😶‍🌫️: ```{name}```\nⓅ︎Ⓡ︎Ⓘ︎Ⓒ︎Ⓔ︎🤑: ```{price}```\n\n"
    except Exception as e:
        logging.error(f"Unexpected Error: {e}")
        return None
    return result

def get_subjects(batch_id, auth_code):
    headers = {
        'authorization': f"Bearer {auth_code}",
        'client-id': '5eb393ee95fab7468a79d189',
        'user-agent': 'Android',
    }
    try:
        response = requests.get(
            f'https://api.penpencil.xyz/v3/batches/{batch_id}/details',
            headers=headers,
            timeout=10,
        )
        response.raise_for_status()
        data = response.json().get("data", {})
        return data.get("subjects", [])
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to fetch subjects: {e}")
        return []

def get_batch_contents(batch_id, subject_id, page, auth_code, content_type):
    headers = {
        'authorization': f"Bearer {auth_code}",
        'client-id': '5eb393ee95fab7468a79d189',
        'user-agent': 'Android',
    }
    params = {'page': page, 'contentType': content_type}
    try:
        response = requests.get(
            f'https://api.penpencil.xyz/v2/batches/{batch_id}/subject/{subject_id}/contents',
            params=params,
            headers=headers,
            timeout=10,
        )
        response.raise_for_status()
        return response.json().get("data", [])
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to fetch batch contents: {e}")
        return []

def save_batch_contents(batch_name, subject_name, subject_data):
    filename = f"{batch_name}_{subject_name}.txt"
    file_path = os.path.join(DOWNLOAD_DIR, filename)
    with open(file_path, 'a', encoding='utf-8') as file:
        for data in subject_data:
            file.write(f"{data['title']}: {data['url']}\n")
    logging.info(f"Contents saved to {file_path}")
    return file_path

# Bot Handlers
async def pw_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("𝕊𝕖𝕟𝕕 𝕪𝕠𝕦𝕣 ℙ𝕎 𝕒𝕦𝕥𝕙𝕖𝕟𝕥𝕚𝕔𝕒𝕥𝕚𝕠𝕟 𝕔𝕠𝕕𝕖😗[𝕋𝕠𝕜𝕖𝕟]:")
    return AUTH_CODE

async def handle_auth_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    auth_code = update.message.text.strip()
    context.user_data['auth_code'] = auth_code
    await update.message.reply_text("𝐅𝐞𝐭𝐜𝐡𝐢𝐧𝐠 𝐘𝐨𝐮𝐫 𝐁𝐚𝐭𝐜𝐡𝐞𝐬. 𝐏𝐥𝐞𝐚𝐬𝐞 𝐖𝐚𝐢𝐭✋...")
    batches = get_batches(auth_code)
    if batches is None:
        await update.message.reply_text("Failed to fetch batches. Please check your token and try again.")
        return ConversationHandler.END
    if not batches.strip():
        await update.message.reply_text("No batches found or failed to fetch. Please check your token.")
        return ConversationHandler.END
    await update.message.reply_text(
        f"𝒀𝒐𝒖𝒓 𝑩𝒂𝒕𝒄𝒉𝒆𝒔😉:\n\n{batches}\n\n𝑺𝒆𝒏𝒅 𝒕𝒉𝒆 𝑩𝒂𝒕𝒄𝒉 𝑰𝑫 𝑻𝑶 𝑷𝒓𝒐𝒄𝒆𝒆𝒅⏳:",
        parse_mode="Markdown",
    )
    return BATCH_ID

async def handle_batch_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    batch_id = update.message.text.strip()
    context.user_data['batch_id'] = batch_id
    auth_code = context.user_data['auth_code']
    subjects = get_subjects(batch_id, auth_code)
    if not subjects:
        await update.message.reply_text("𝑁𝑜 𝑠𝑢𝑏𝑗𝑒𝑐𝑡𝑠 𝑓𝑜𝑢𝑛𝑑 𝑓𝑜𝑟 𝑡ℎ𝑖𝑠 𝑏𝑎𝑡𝑐ℎ.")
        return ConversationHandler.END
    subject_list = "\n".join([f"```{subject['_id']}```: ```{subject['subject']}```" for subject in subjects])
    await update.message.reply_text(
        f"𝚂𝚞𝚋𝚓𝚎𝚌𝚝𝚜 𝚏𝚘𝚞𝚗𝚍:\n{subject_list}\n\n𝚂𝚎𝚗𝚍 𝚝𝚑𝚎 𝚂𝚞𝚋𝚓𝚎𝚌𝚝 𝙸𝙳(s) to fetch contents (separate multiple IDs with '&'):"
    )
    return SUBJECT_IDS

async def handle_subject_ids(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['subject_ids'] = update.message.text.strip().split('&')
    keyboard = [
        [
            InlineKeyboardButton("Exercises", callback_data="exercises-notes-videos"),
            InlineKeyboardButton("Notes", callback_data="notes"),
        ],
        [
            InlineKeyboardButton("DppNotes", callback_data="DppNotes"),
            InlineKeyboardButton("DppSolution", callback_data="DppSolution"),
        ],
        [
            InlineKeyboardButton("Cancel", callback_data="cancel"),
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Choose the type of content to extract:", reply_markup=reply_markup)

async def extract_content(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "cancel":
        await query.edit_message_text("Operation cancelled.")
        return ConversationHandler.END

    content_type = query.data
    auth_code = context.user_data['auth_code']
    batch_id = context.user_data['batch_id']
    subject_ids = context.user_data['subject_ids']
    await query.edit_message_text(f"Extracting content type: {content_type}. Please wait...")

    for subject_id in subject_ids:
        page = 1
        processed_data = []
        while True:
            subject_data = get_batch_contents(batch_id, subject_id, page, auth_code, content_type)
            if not subject_data:
                break
            if content_type == "exercises-notes-videos":
                for item in subject_data:
                    processed_data.append({'title': item['topic'], 'url': item['url'].strip()})
            elif content_type == "notes":
                for item in subject_data:
                    if item.get('homeworkIds'):
                        homework = item['homeworkIds'][0]
                        if homework.get('attachmentIds'):
                            attachment = homework['attachmentIds'][0]
                            processed_data.append({
                                'title': homework['topic'],
                                'url': attachment['baseUrl'] + attachment['key']
                            })
            elif content_type == "DppNotes":
                for item in subject_data:
                    if item.get('homeworkIds'):
                        for homework in item['homeworkIds']:
                            if homework.get('attachmentIds'):
                                attachment = homework['attachmentIds'][0]
                                processed_data.append({
                                    'title': homework['topic'],
                                    'url': attachment['baseUrl'] + attachment['key']
                                })
            elif content_type == "DppSolution":
                for item in subject_data:
                    url = item['url'].replace("d1d34p8vz63oiq", "d26g5bnklkwsh4").replace("mpd", "m3u8").strip()
                    processed_data.append({'title': item['topic'], 'url': url})
            page += 1

        if processed_data:
            subject_name = f"Subject_{subject_id}"
            file_path = save_batch_contents(batch_id, subject_name, processed_data)
            with open(file_path, 'rb') as file:
                await query.message.reply_document(file, caption=f"Content extracted for: {subject_name}")
            os.remove(file_path)
        else:
            await query.message.reply_text(f"No content found for Subject ID: {subject_id}.")

# Add Handlers to the Dispatcher
pw_handler = ConversationHandler(
    entry_points=[CommandHandler("pw", pw_start)],
    states={
        AUTH_CODE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_auth_code)],
        BATCH_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_batch_id)],
        SUBJECT_IDS: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_subject_ids)],
    },
    fallbacks=[],
)

callback_handler = CallbackQueryHandler(extract_content)
