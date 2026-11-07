import logging
import os

from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from translator_service import TranslatorService, ChineseTranslator

load_dotenv()

logging.basicConfig(
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    level=logging.INFO,
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger: logging.Logger = logging.getLogger(__name__)



def load_max_words() -> int:
    """Read and validate MAX_MESSAGE_WORDS from the environment."""
    raw_value: str | None = os.getenv("MAX_MESSAGE_WORDS", "100")

    try:
        max_words: int = int(raw_value) if raw_value is not None else 100
    except ValueError as error:
        raise RuntimeError("MAX_MESSAGE_WORDS must be an integer.") from error

    if max_words < 1:
        raise RuntimeError("MAX_MESSAGE_WORDS must be greater than zero.")

    return max_words


async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    message = update.effective_message
    if message is None:
        logger.warning("Start command received without an effective message.")
        return

    await message.reply_text(
        "Forward me a text message to get started. "
        "Translation isn't enabled yet."
    )


async def help_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    message = update.effective_message
    if message is None:
        logger.warning("Help command received without an effective message.")
        return

    await message.reply_text(
        "Forward a text message to this bot. "
        "For now, I will prepare the text for translation."
    )
    
async def list_words(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    message = update.effective_message
    if message is None:
        return

    service: TranslatorService = (
        context.application.bot_data["translator_service"]
    )
    seen_words = sorted(
        service.seen_words.values(),
        key=lambda word: word.normalized,
    )

    if not seen_words:
        await message.reply_text("No words have been recorded yet.")
        return

    header = " # | Word | Normalized\n---|---|---"
    pages: list[list[str]] = []
    current_rows: list[str] = [header]

    for index, word in enumerate(seen_words, start=1):
        row = f"{index} | {word.text} | {word.normalized}"
        candidate = "\n".join([*current_rows, row])

        # Leave room for the heading and stay below Telegram's message limit.
        if len(candidate) + 100 > 4000 and len(current_rows) > 1:
            pages.append(current_rows)
            current_rows = [header]

        current_rows.append(row)

    if len(current_rows) > 1:
        pages.append(current_rows)

    for page_number, rows in enumerate(pages, start=1):
        heading = f"Seen words ({len(seen_words)})"
        if len(pages) > 1:
            heading += f" — page {page_number}/{len(pages)}"

        await message.reply_text(f"{heading}\n" + "\n".join(rows))



async def handle_forwarded_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    message = update.effective_message
    if message is None:
        logger.warning("Update received without an effective message.")
        return

    is_forwarded: bool = (
        message.forward_origin is not None or message.forward_date is not None
    )
    if not is_forwarded:
        await message.reply_text("Please forward a text message to get started.")
        return

    # For a forwarded photo, this processes only its caption, if present.
    # The bot does not download or inspect the picture.
    source_text: str | None = message.text or message.caption
    if source_text is None or not source_text.strip():
        logger.info("Forwarded message contained no text or caption.")
        await message.reply_text(
            "I couldn't find text in that message. "
            "Pictures without captions aren't processed."
        )
        return
    translator_service: TranslatorService = context.application.bot_data["translator_service"]
    try:
        prepared = translator_service.prepare_message(source_text)
    except (TypeError, ValueError):
        logger.exception("Failed to prepare forwarded message text.")
        await message.reply_text("I couldn't prepare that message. Please try again.")
        return
    except Exception:
        logger.exception("Unexpected error while preparing forwarded message text.")
        await message.reply_text("Something went wrong while processing that message.")
        return

    if not prepared.chunks:
        logger.info("Message contained no text after sanitization.")
        await message.reply_text(
            "There was no usable text after removing links and symbols."
        )
        return

    logger.info("Forwarded message prepared successfully.")

        
    for index, chunk in enumerate(prepared.chunks, start=1):
        await message.reply_text(f"Chunk {index}/{len(prepared.chunks)}:\n{chunk}")

    new_word_count = sum(word.is_new for word in prepared.words)

    await message.reply_text(
        f"Post-processing complete.\n"
        f"Words: {len(prepared.words)}\n"
        f"Chunks: {len(prepared.chunks)}\n"
        f"New words: {new_word_count}"
    )




async def error_handler(
    update: object,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    error: object | None = context.error
    logger.error(
        "Unhandled error while processing an update.",
        exc_info=error if isinstance(error, BaseException) else None,
    )


def main() -> None:
    token: str | None = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token or not token.strip():
        raise RuntimeError(
            "TELEGRAM_BOT_TOKEN is missing or empty. Check your .env file."
        )

    application: Application = Application.builder().token(token).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("list", list_words))
    application.add_handler(
        MessageHandler(
            (filters.TEXT | filters.CAPTION) & ~filters.COMMAND,
            handle_forwarded_message,
        )
    )
    application.add_error_handler(error_handler)

    logger.info("Starting Telegram bot polling.")
    application.bot_data["translator_service"] = ChineseTranslator(load_max_words())
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
