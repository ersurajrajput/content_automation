"""Abstract subtitle translator interface."""
from abc import ABC, abstractmethod


class SubtitleTranslator(ABC):
    """Abstract base for all subtitle translation backends."""

    @abstractmethod
    def is_configured(self) -> bool:
        """Return True if the translator has valid credentials/config."""
        ...

    @abstractmethod
    def translate(
        self,
        subtitle_path: str,
        source_language: str,
        target_language: str,
    ) -> str:
        """
        Translate a subtitle file.

        Args:
            subtitle_path: Absolute path to source .srt or .ass file.
            source_language: Source language name (e.g. 'English').
            target_language: Target language name (e.g. 'Hindi').

        Returns:
            Absolute path to the translated subtitle file.

        Raises:
            TranslationError: If translation fails.
        """
        ...

    @property
    def display_name(self) -> str:
        return "Unknown Translator"


class TranslationError(Exception):
    """Raised when a translation operation fails."""
    pass


class TranslationNotConfiguredError(TranslationError):
    """Raised when no translation API is configured."""
    pass
