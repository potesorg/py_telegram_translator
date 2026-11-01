# Telegram Translator Bot

A Telegram bot that translates forwarded messages using a locally hosted TranslateGemma model served by Ollama.

For the demo, a user forwards a Spanish message to the bot. The bot detects the source language, translates the message into English, and returns a word-and-phrase breakdown with any context needed to understand the message.

## 🌟 Demo Example

**User forwards a message:**
> "No me tomes el pelo, que ya sé cómo va esto."

**Bot response:**
**Detected Language:** Spanish 🇪🇸
**English Translation:** "Don't pull my leg; I already know how this works."

**Word & Phrase Breakdown:**
- `No me tomes el pelo` $\rightarrow$ (Idiom) Literally "don't take my hair," meaning "don't fool me."
- `Ya sé` $\rightarrow$ "I already know."
- `Cómo va esto` $\rightarrow$ "How this goes/works."

**Contextual Meaning:**
The speaker is expressing skepticism and signaling that they are aware of the true nature of the situation.

---

## ⚙️ How It Works

1. The user forwards a foreign-language message to the Telegram bot.
2. The bot extracts the message text.
3. The bot sends the text to the local Ollama server.
4. TranslateGemma identifies the language and produces an English translation.
5. The bot requests a separate word/phrase breakdown and contextual explanation.
6. The bot formats and sends the result back to the user.

## 🏗️ Architecture

- **Telegram Bot:** Receives forwarded messages and sends replies.
- **Ollama:** Runs locally and exposes the TranslateGemma model via a REST API.
- **TranslateGemma:** Detects the source language and provides the core translation.
- **Explanation Layer:** A secondary prompt sequence that analyzes the translation to produce the linguistic breakdown and contextual notes.

## 🗺️ Roadmap

- [ ] Implement Telegram bot message listener for forwarded texts
- [ ] Integrate Ollama API for communication with the local server
- [ ] Configure TranslateGemma for automatic language detection
- [ ] Develop the prompt engineering for English translation output
- [ ] Create a logic flow for generating the word-by-word breakdown
- [ ] Build the "contextual meaning" inference system
- [ ] Design the final response template for a clean user experience in Telegram
