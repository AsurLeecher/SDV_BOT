import logging
import os
import requests
import itertools
from telegram import Update
from telegram.ext import (
    CommandHandler,
    ConversationHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# Constants
LOG_GROUP_ID = -1002385500773
ROOT_DIR = os.getcwd()

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
            response = requests.get(
                f'https://api.penpencil.xyz/v3/batches/my-batches?page={page}&mode=1',
                headers=headers,
            )
            if response.status_code == 401:
                # Token invalid or expired
                raise ValueError("Invalid or expired token")

            if response.status_code != 200:
                logging.error(f"Failed to fetch batches. Status code: {response.status_code}")
                break

            data = response.json().get("data", [])
            if not data:
                break

            for batch in data:
                batch_id = batch["_id"]
                name = batch["name"]
                price = batch.get("feeId", {}).get("total", "Free")
                result += f"𝑩𝒂𝒕𝒄𝒉 𝑰𝑫💡: ```{batch_id}```\n𝑩𝒂𝒕𝒄𝒉 𝑵𝒂𝒎𝒆😶‍🌫️: ```{name}```\nⓅ︎Ⓡ︎Ⓘ︎Ⓒ︎Ⓔ︎🤑: ```{price}```\n\n"
    except ValueError as ve:
        logging.error(f"Token Error: {ve}")
        return "TOKEN_ERROR"
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

    response = requests.get(f'https://api.penpencil.xyz/v3/batches/{batch_id}/details', headers=headers)
    if response.status_code == 200:
        data = response.json().get("data", {})
        return data.get("subjects", [])
    else:
        logging.error(f"Failed to fetch subjects. Status code: {response.status_code}")
        return []

def get_batch_contents(batch_id, subject_id, page, auth_code):
    headers = {
        'authorization': f"Bearer {auth_code}",
        'client-id': '5eb393ee95fab7468a79d189',
        'user-agent': 'Android',
    }

    params = {'page': page, 'contentType': 'exercises-notes-videos'}
    response = requests.get(f'https://api.penpencil.xyz/v2/batches/{batch_id}/subject/{subject_id}/contents', params=params, headers=headers)
    if response.status_code == 200:
        return response.json().get("data", [])
    else:
        logging.error(f"Failed to fetch batch contents. Status code: {response.status_code}")
        return []

def save_batch_contents(batch_name, subject_name, subject_data):
    filename = f"{batch_name}_{subject_name}.txt"
    file_path = os.path.join(ROOT_DIR, filename)
    with open(file_path, 'a', encoding='utf-8') as file:
        for data in subject_data:
            class_title = data.get("topic", "Unknown")
            class_url = data.get("url", "").strip()
            if class_url:
                file.write(f"{class_title}: {class_url}\n")
    logging.info(f"Contents saved to {file_path}")
    return file_path
# Other helper functions: get_subjects, get_batch_contents, save_batch_contents 
# (Aapke code mein jo existing hai, wo copy karenge bina kuch missing kiye).

# Bot Handlers
async def pw_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("𝕊𝕖𝕟𝕕 𝕪𝕠𝕦𝕣 𝕒𝕦𝕥𝕙𝕖𝕟𝕥𝕚𝕔𝕒𝕥𝕚𝕠𝕟 𝕔𝕠𝕕𝕖😗[𝕋𝕠𝕜𝕖𝕟]:")
    return AUTH_CODE

async def handle_auth_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        auth_code = update.message.text.strip()
        context.user_data['auth_code'] = auth_code

        # Fetch Batches
        await update.message.reply_text("Fetching your batches. Please wait...")
        batches = get_batches(auth_code)

        if batches == "TOKEN_ERROR":
            await update.message.reply_text("Invalid or expired token. Please provide a valid token.")
            return ConversationHandler.END

        if not batches or not batches.strip():
            await update.message.reply_text("No batches found or failed to fetch. Please check your token.")
            return ConversationHandler.END

        await update.message.reply_text(
            f"Your Batches😉:\n\n{batches}\n\nSend the Batch ID to proceed:",
            parse_mode="Markdown",
        )
        return BATCH_ID
    except Exception as e:
        logging.error(f"Error in handle_auth_code: {e}")
        await update.message.reply_text("An error occurred. Please try again later.")
        return ConversationHandler.END

# Other handlers: handle_batch_id, handle_subject_ids 
# (Yeh aapke existing code se as-is re-use karenge).
async def handle_batch_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle Batch ID input."""
    batch_id = update.message.text.strip()
    context.user_data['batch_id'] = batch_id
    auth_code = context.user_data['auth_code']

    # Fetch Subjects
    subjects = get_subjects(batch_id, auth_code)
    if not subjects:
        await update.message.reply_text("No subjects found for this batch.")
        return ConversationHandler.END

    subject_list = "\n".join([f"{subject['_id']}: {subject['subject']}" for subject in subjects])
    await update.message.reply_text(f"𝚂𝚞𝚋𝚓𝚎𝚌𝚝𝚜 𝚏𝚘𝚞𝚗𝚍:\n{subject_list}\n\n𝚂𝚎𝚗𝚍 𝚝𝚑𝚎 𝚂𝚞𝚋𝚓𝚎𝚌𝚝 𝙸𝙳(s) to fetch contents (separate multiple IDs with '&'):")
    context.user_data['subjects'] = subjects
    return SUBJECT_IDS

async def handle_subject_ids(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle Subject IDs input."""
    auth_code = context.user_data['auth_code']
    batch_id = context.user_data['batch_id']
    subjects = context.user_data['subjects']

    subject_ids = update.message.text.strip().split('&')
    await update.message.reply_text("Link extraction started. Please wait...")

    for subject_id in subject_ids:
        page = 1
        all_subject_data = []
        while True:
            subject_data = get_batch_contents(batch_id, subject_id, page, auth_code)
            if not subject_data:
                break
            all_subject_data.extend(subject_data)
            page += 1

        if all_subject_data:
            subject_name = next(
                (subject['subject'] for subject in subjects if subject['_id'] == subject_id), f"Subject_{subject_id}"
            )
            file_path = save_batch_contents(batch_id, subject_name, all_subject_data)

            # Send the file to the user
            try:
                with open(file_path, 'rb') as file:
                    await update.message.reply_document(file, caption=f"Contents for {subject_name}.")
            except Exception as e:
                await update.message.reply_text(f"Error sending file to user: {e}")
                continue
                # Send to Log Group
            try:
                with open(file_path, 'rb') as file:
                    await context.bot.send_document(
                        chat_id=LOG_GROUP_ID,
                        document=file,
                        caption=f"Contents for {subject_name} saved and sent to the user.",
                    )
                logging.info(f"File {file_path} successfully sent to log group.")
            except Exception as e:
                await update.message.reply_text(f"Error sending file to log group: {e}")
                logging.error(f"Error sending file to log group: {e}")
                continue

            # Delete the temporary file after sending
            try:
                os.remove(file_path)
                logging.info(f"Temporary file {file_path} deleted after sending.")
            except Exception as e:
                logging.error(f"Error deleting temporary file: {e}")
        else:
            await update.message.reply_text(f"No content found for subject ID🤐 {subject_id}.")

    return ConversationHandler.END

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    """Log errors."""
    logging.error(f"Exception: {context.error}")
    try:
        await context.bot.send_message(chat_id=LOG_GROUP_ID, text=f"Error: {context.error}")
    except Exception as e:
        logging.error(f"Failed to log error: {e}")

    return ConversationHandler.END
# Combine everything into pw_handler
pw_handler = ConversationHandler(
    entry_points=[CommandHandler("pw", pw_start)],
    states={
        AUTH_CODE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_auth_code)],
        BATCH_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_batch_id)],
        SUBJECT_IDS: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_subject_ids)],
    },
    fallbacks=[],
)