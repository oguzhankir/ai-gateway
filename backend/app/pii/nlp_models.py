"""spaCy NLP models singleton."""

from typing import Optional
import spacy
from spacy.language import Language


class NLPModels:
    """Singleton for managing spaCy models."""

    _instance: Optional["NLPModels"] = None
    _turkish_model: Optional[Language] = None
    _english_model: Optional[Language] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def get_turkish_model(self) -> Language:
        """
        Get Turkish spaCy model (lazy loading).

        Returns:
            Turkish spaCy model
        """
        if self._turkish_model is None:
            try:
                self._turkish_model = spacy.load("tr_core_news_lg")
            except OSError:
                # Fallback to medium model if large not available
                try:
                    self._turkish_model = spacy.load("tr_core_news_md")
                except OSError:
                    # Fallback to small model
                    self._turkish_model = spacy.load("tr_core_news_sm")
        return self._turkish_model

    def get_english_model(self) -> Language:
        """
        Get English spaCy model (lazy loading).

        Returns:
            English spaCy model
        """
        if self._english_model is None:
            try:
                self._english_model = spacy.load("en_core_web_lg")
            except OSError:
                # Fallback to medium model if large not available
                try:
                    self._english_model = spacy.load("en_core_web_md")
                except OSError:
                    # Fallback to small model
                    self._english_model = spacy.load("en_core_web_sm")
        return self._english_model

    def detect_language(self, text: str) -> str:
        """
        Simple language detection (basic heuristic).

        Args:
            text: Text to analyze

        Returns:
            Language code ("tr" or "en")
        """
        # Simple heuristic: check for Turkish characters
        turkish_chars = "çğıöşüÇĞIİÖŞÜ"
        if any(char in text for char in turkish_chars):
            return "tr"
        return "en"


# Singleton instance
nlp_models = NLPModels()

