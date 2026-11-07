import logging
import re
import unicodedata
from abc import ABC, abstractmethod
from ollama import QwenService
from dataclasses import dataclass, replace

import jieba

logger: logging.Logger = logging.getLogger(__name__)

_URL_PATTERN: re.Pattern[str] = re.compile(
    r"""(?ix)
    \b
    (?:
        https?://
        |
        www\.
        |
        [a-z0-9.-]+\.[a-z]{2,}(?:/[^\s]*)?
    )
    [^\s]*
    """
)


@dataclass(frozen=True)
class Word:
    text: str
    normalized: str
    is_new: bool


@dataclass(frozen=True)
class PreparedMessage:
    """Text prepared for a future translation step."""

    words: tuple[Word, ...]
    chunks: tuple[str, ...]
    removed_links: int
    removed_symbols: int

class TranslatorService(ABC):
    """Shared text preparation with language-specific word splitting."""

    def __init__(self, max_words: int) -> None:
        if max_words < 1:
            raise ValueError("max_words must be a positive integer")

        self.max_words = max_words
        self.seen_words: dict[str, Word] = {}

    @abstractmethod
    def _split_words(self, text: str) -> list[str]:
        """Split cleaned text into language-specific words."""
        raise NotImplementedError

    def _clean_text(self, text: str) -> tuple[str, int, int]:
        text_without_links, removed_links = _URL_PATTERN.subn(" ", text)

        cleaned_characters: list[str] = []
        removed_symbols = 0

        for character in text_without_links:
            if unicodedata.category(character).startswith("S"):
                cleaned_characters.append(" ")
                removed_symbols += 1
            else:
                cleaned_characters.append(character)

        cleaned_text = re.sub(
            r"\s+", " ", "".join(cleaned_characters)
        ).strip()

        return cleaned_text, removed_links, removed_symbols

    def _record_words(self, words: list[str]) -> tuple[Word, ...]:
        entries: list[Word] = []

        for text in words:
            normalized = text.casefold()
            is_new = normalized not in self.seen_words
            word = Word(text=text, normalized=normalized, is_new=is_new)
            entries.append(word)

            if is_new:
                self.seen_words[normalized] = word

        return tuple(entries)

    def prepare_message(self, text: str) -> PreparedMessage:
        if not isinstance(text, str):
            raise TypeError("text must be a string")

        cleaned_text, removed_links, removed_symbols = self._clean_text(text)
        word_entries = self._record_words(self._split_words(cleaned_text))

        chunks = tuple(
            " ".join(
                word.text
                for word in word_entries[index : index + self.max_words]
            )
            for index in range(0, len(word_entries), self.max_words)
        )

        logger.info(
            "Prepared text: words=%d chunks=%d new_words=%d "
            "links_removed=%d symbols_removed=%d",
            len(word_entries),
            len(chunks),
            sum(word.is_new for word in word_entries),
            removed_links,
            removed_symbols,
        )

        return PreparedMessage(
            words=word_entries,
            chunks=chunks,
            removed_links=removed_links,
            removed_symbols=removed_symbols,
        )


class ChineseTranslator(TranslatorService):
    """Prepares Chinese text using jieba word segmentation."""


    def __init__(self, max_words: int) -> None:
        super().__init__(max_words)
        self.qwen_service = QwenService()


    @staticmethod
    def _is_han_character(character: str) -> bool:
        codepoint = ord(character)
        return (
            0x3400 <= codepoint <= 0x4DBF
            or 0x4E00 <= codepoint <= 0x9FFF
            or 0xF900 <= codepoint <= 0xFAFF
            or 0x20000 <= codepoint <= 0x2EBEF
            or 0x30000 <= codepoint <= 0x323AF
        )

    def _split_words(self, text: str) -> list[str]:
        return [
            token
            for token in jieba.lcut(text)
            if token and all(self._is_han_character(char) for char in token)
        ]

    def _record_words(self, words):
        entries: list[Word] = []

        for text in words:
            normalized = text.casefold()
            is_new = normalized not in self.seen_words
            word = Word(text=text, normalized=normalized, is_new=is_new)
            entries.append(word)

            if is_new:
                self.seen_words[normalized] = word

        self.seen_words = dict(
            sorted(
                (
                    (normalized, word)
                    for normalized, word in self.seen_words.items()
                    if all(
                        ChineseTranslator._is_han_character(char)
                        for char in word.text
                    )
                ),
                key=lambda item: item[1].normalized,
            )
        )

        logger.info("Saved %d words", len(self.seen_words))


        return tuple(entries)
    

    def prepare_message(self, text: str) -> PreparedMessage:
        prepared = super().prepare_message(text)

        translated_chunks: list[str] = []

        for original_chunk in prepared.chunks:
            translated_text = self.qwen_service.translate(
                text=original_chunk
            ).strip()

            # Keep any list-style breakdown returned by the model.
            entries: list[str] = []
            for line in translated_text.splitlines():
                line = line.strip()
                if not line:
                    continue

                if line.startswith(("- ", "* ")):
                    line = line[2:].strip()

                entries.append(line)

            translation = "\n".join(entries)

            logger.info(
                "[original] - %s\n[translated] - %s",
                original_chunk,
                translation,
            )

            translated_chunks.append(
                f"[original]\n{original_chunk}\n[translated]\n{translation}"
            )

        return replace(prepared, chunks=tuple(translated_chunks))


    def _split_words(self, text: str) -> list[str]:
        return [word for word in jieba.lcut(text) if word.strip()]
