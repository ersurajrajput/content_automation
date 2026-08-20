"""Translation service implementation (placeholder with provider support)."""
import os
import re
from pathlib import Path

from video_automator.services.translation.base import (
    SubtitleTranslator,
    TranslationError,
    TranslationNotConfiguredError,
)
from video_automator.config.settings import get_settings


class TranslationService(SubtitleTranslator):
    """
    Configurable translation service.

    Currently provides a placeholder implementation.
    To enable real translation, configure `translation_provider` and
    `translation_api_key` in application settings.

    Supported providers (future):
        - 'google'    → Google Cloud Translation API
        - 'deepl'     → DeepL API
        - 'azure'     → Azure Cognitive Services Translator
        - 'libretranslate' → LibreTranslate (self-hosted, free)
    """

    PROVIDER_DISPLAY_NAMES = {
        "google": "Google Cloud Translate",
        "deepl": "DeepL",
        "azure": "Azure Translator",
        "libretranslate": "LibreTranslate",
    }

    def __init__(self):
        self._settings = get_settings()

    @property
    def provider(self) -> str:
        return self._settings.translation_provider.lower().strip()

    @property
    def api_key(self) -> str:
        return self._settings.translation_api_key.strip()

    @property
    def display_name(self) -> str:
        return self.PROVIDER_DISPLAY_NAMES.get(self.provider, "Translation Service")

    def is_configured(self) -> bool:
        """Return True only if a provider and API key are both set."""
        return bool(self.provider) and bool(self.api_key)

    def translate(
        self,
        subtitle_path: str,
        source_language: str,
        target_language: str,
    ) -> str:
        """
        Translate subtitle file to target language.
        
        Raises TranslationNotConfiguredError if no API is configured.
        """
        if not self.is_configured():
            raise TranslationNotConfiguredError(
                "No translation provider is configured.\n\n"
                "To enable subtitle translation, go to Settings and configure:\n"
                "  • Translation Provider (e.g. Google, DeepL)\n"
                "  • API Key\n\n"
                "You can still use the original subtitles without translation."
            )

        src = Path(subtitle_path)
        if not src.exists():
            raise TranslationError(f"Subtitle file not found: {subtitle_path}")

        out_path = src.parent / f"{src.stem}_{target_language.lower()}{src.suffix}"

        if self.provider == "libretranslate":
            return self._translate_libretranslate(
                subtitle_path, str(out_path), source_language, target_language
            )
        else:
            raise TranslationError(
                f"Provider '{self.provider}' is configured but not yet implemented.\n"
                "Please use 'libretranslate' or implement the provider adapter."
            )

    def _translate_libretranslate(
        self,
        subtitle_path: str,
        output_path: str,
        source_language: str,
        target_language: str,
    ) -> str:
        """Translate using LibreTranslate REST API."""
        try:
            import urllib.request
            import json
        except ImportError:
            raise TranslationError("urllib not available")

        LANG_CODES = {
            "english": "en", "hindi": "hi", "spanish": "es", "french": "fr",
            "german": "de", "portuguese": "pt", "bengali": "bn", "tamil": "ta",
            "telugu": "te", "marathi": "mr", "gujarati": "gu", "japanese": "ja",
            "chinese": "zh", "arabic": "ar", "russian": "ru", "korean": "ko",
        }
        src_code = LANG_CODES.get(source_language.lower(), "en")
        tgt_code = LANG_CODES.get(target_language.lower(), "hi")

        endpoint = "http://localhost:5000/translate"

        with open(subtitle_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Split SRT into blocks, translate text lines only
        blocks = re.split(r"\n\n+", content.strip())
        translated_blocks = []

        for block in blocks:
            lines = block.split("\n")
            if len(lines) < 3:
                translated_blocks.append(block)
                continue
            header = lines[:2]  # index + timestamp
            text_lines = lines[2:]
            text = "\n".join(text_lines)

            payload = json.dumps({
                "q": text,
                "source": src_code,
                "target": tgt_code,
                "api_key": self.api_key,
            }).encode("utf-8")
            req = urllib.request.Request(
                endpoint,
                data=payload,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            try:
                with urllib.request.urlopen(req, timeout=30) as resp:
                    result = json.loads(resp.read().decode("utf-8"))
                translated_text = result.get("translatedText", text)
            except Exception as e:
                raise TranslationError(f"LibreTranslate request failed: {e}")

            translated_blocks.append("\n".join(header) + "\n" + translated_text)

        with open(output_path, "w", encoding="utf-8") as f:
            f.write("\n\n".join(translated_blocks) + "\n")

        return output_path
