# Telegram Translator Bot

A Telegram bot project for translating forwarded messages with a locally hosted TranslateGemma model served by Ollama.

The current implementation prepares forwarded text, splits it into word-limited chunks, and tracks vocabulary. The Ollama translation and explanation steps are still planned.

## Current Functionality

- Handles forwarded text messages and captions.
- Removes URLs and Unicode symbols from the text before processing.
- Splits prepared text into chunks according to `MAX_MESSAGE_WORDS`.
- Uses a `TranslatorService` interface so language-specific word segmentation can be implemented by subclasses.
- Includes `ChineseTranslator`, which uses `jieba` to segment text and keeps only tokens made entirely of Han characters.
- Tracks unique words as `Word` dataclass entries. Each entry records the original text, normalized form, and whether it was new when encountered.
- Provides `/list`, which displays the tracked vocabulary in a table-like format.
- Reports the prepared word and chunk counts after sending the chunks.

The tracked vocabulary is held in memory, so it resets when the bot restarts.

## Example

A user forwards a message containing Chinese text. The bot prepares and sends its chunks, then reports the word and chunk counts. Use `/list` to view the unique Han-character words recorded by the bot.

## Planned Translation Flow

The intended end-to-end workflow is:

1. The user forwards a foreign-language message to the bot.
2. The bot extracts the message text or caption.
3. The bot sends the text to the local Ollama server.
4. TranslateGemma identifies the source language and translates the message into English.
5. A separate explanation step generates a word-and-phrase breakdown and contextual meaning.
6. The bot formats and sends the translation and explanation to the user.

## Architecture

- **Telegram bot:** Receives forwarded messages and sends replies.
- **`TranslatorService`:** Shared interface and processing logic for cleaning, tracking, and chunking text.
- **`ChineseTranslator`:** Implements Chinese word segmentation with `jieba`.
- **Ollama and TranslateGemma:** Planned translation backend.
- **Explanation layer:** Planned separate prompt step for phrase breakdown and context.

## Configuration

Create a `.env` file:

```env
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
MAX_MESSAGE_WORDS=100
```

`MAX_MESSAGE_WORDS` controls the maximum number of segmented words per chunk. For Chinese, a segmented word may contain multiple characters.

## Roadmap

- [x] Handle forwarded text and captions
- [x] Remove links and Unicode symbols before processing
- [x] Split prepared text into configurable chunks
- [x] Add language-specific word segmentation through `TranslatorService`
    - [x] Add Chinese segmentation and Han-character filtering
- [x] Track unique words and list them with `/list`
- [ ] Integrate the local Ollama API
- [ ] Configure TranslateGemma translation and source-language detection
- [ ] Generate word-and-phrase breakdowns
- [ ] Generate contextual explanations
- [ ] Format and send the complete translation response in Telegram