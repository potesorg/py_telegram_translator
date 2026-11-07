import requests


class QwenService:
    # Override the model's bundled translation-only template.
    CHAT_TEMPLATE = """{{ if .System }}<|im_start|>system
{{ .System }}<|im_end|>
{{ end }}<|im_start|>user
You are a professional multilingual translation engine. Your ONLY function is to translate text.
{{ .Prompt }}<|im_end|>
<|im_start|>assistant
"""

    SYSTEM_PROMPT = """Create an ordered Chinese word list with pinyin and English meanings.

For each meaningful Chinese word or short expression, output one line in this format:
- Chinese text (pinyin) — English meaning

Rules:
- Copy each Chinese text entry exactly from the source.
- Do not think about the translation
- Keep entries in source order. Together, their Chinese text must cover the source
  characters in order, without adding, omitting, or repeating characters.
- Do not create entries for words or characters that are not in the source.
- Do not list punctuation as a separate entry.
- Give tone-marked pinyin for the Chinese text in each entry.
- Translate only what the source supports; do not invent context.
- Return only the list. Do not include a heading, explanation, or sentence translation."""

    def __init__(
        self,
        model: str = "kaelri/qwen3.5-mt:2b",
        base_url: str = "http://localhost:11434",
    ):
        self.model = model
        self.generate_url = f"{base_url.rstrip('/')}/api/generate"
        self.session = requests.Session()

    def translate(self, text: str) -> str:
        if not text.strip():
            return ""

        response = self.session.post(
            self.generate_url,
            json={
                "model": self.model,
                "system": self.SYSTEM_PROMPT,
                "prompt": f"Source text:\n{text}\n\nWord list:",
                "template": self.CHAT_TEMPLATE,
                "think": False,
                "stream": False,
            }, timeout=30
        )
        response.raise_for_status()
        return response.json()["response"].strip()
