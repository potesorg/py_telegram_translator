import logging
import os

from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    Application,
    ContextTypes,
    CommandHandler,
    MessageHandler,
    filters,
)

load_dotenv()

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger: logging.Logger = logging.getLogger(__name__)


async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Explain what the bot can do so far."""
    message = update.effective_message
    if message is None:
        logger.warning("Received /start without an effective message.")
        return

    await message.reply_text(
        "Hi! Forward me a text message to get started. "
        "Translation isn't enabled yet."
    )


async def help_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Show brief usage instructions."""
    message = update.effective_message
    if message is None:
        logger.warning("Received /help without an effective message.")
        return

    await message.reply_text(
        "Forward a text message to this bot. "
        "For now, I can confirm that I received it; translation is coming later."
    )


async def handle_forwarded_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Acknowledge a forwarded text message or caption."""
    message = update.effective_message
    if message is None:
        logger.warning("Received an update without an effective message.")
        return

    is_forwarded: bool = (
        message.forward_origin is not None or message.forward_date is not None
    )
    if not is_forwarded:
        await message.reply_text("Please forward a text message to get started.")
        return

    text: str | None = message.text or message.caption
    if not text or not text.strip():
        await message.reply_text(
            "I received the forwarded message, but it doesn't contain text to process."
        )
        return

    logger.info("Received a forwarded text message.")
    await message.reply_text(
        "Forwarded message received. Translation isn't enabled yet."
    )


async def error_handler(
    update: object,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Log errors raised while handling an update."""
    error: object | None = context.error
    logger.error(
        "An error occurred while processing an update.",
        exc_info=error if isinstance(error, BaseException) else None,
    )


def main() -> None:
    """Build and run the bot."""
    token: str | None = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token or not token.strip():
        raise RuntimeError(
            "TELEGRAM_BOT_TOKEN is missing or empty. "
            "Check that your .env file contains the bot token."
        )

    application: Application = Application.builder().token(token).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(
        MessageHandler(
            (filters.TEXT | filters.CAPTION) & ~filters.COMMAND,
            handle_forwarded_message,
        )
    )
    application.add_error_handler(error_handler)

    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
