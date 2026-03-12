"""
Internationalization (i18n) Module
Handles multi-language support for the application
"""

import yaml
import logging
from pathlib import Path
from typing import Dict, Any


class I18n:
    """Internationalization manager"""
    
    SUPPORTED_LANGUAGES = {
        'en': 'English',
        'he': 'עברית',
        'fr': 'Français'
    }
    
    def __init__(self, default_language='en'):
        self.logger = logging.getLogger(__name__)
        self.current_language = default_language
        self.translations = {}
        self.translations_dir = Path(__file__).parent.parent / 'translations'
        
        # Load all translations
        self.load_all_translations()
        
        # Set default language
        self.set_language(default_language)
    
    def load_all_translations(self):
        """Load all available translation files"""
        if not self.translations_dir.exists():
            self.logger.warning(f"Translations directory not found: {self.translations_dir}")
            return
        
        for lang_code in self.SUPPORTED_LANGUAGES.keys():
            lang_file = self.translations_dir / f"{lang_code}.yaml"
            if lang_file.exists():
                try:
                    with open(lang_file, 'r', encoding='utf-8') as f:
                        self.translations[lang_code] = yaml.safe_load(f)
                    self.logger.info(f"Loaded {lang_code} translations")
                except Exception as e:
                    self.logger.error(f"Failed to load {lang_code} translations: {e}")
    
    def set_language(self, language_code: str):
        """Set current application language"""
        if language_code not in self.SUPPORTED_LANGUAGES:
            self.logger.warning(f"Unsupported language: {language_code}, using English")
            language_code = 'en'
        
        self.current_language = language_code
        self.logger.info(f"Language set to: {self.SUPPORTED_LANGUAGES[language_code]}")
    
    def get_language(self) -> str:
        """Get current language code"""
        return self.current_language
    
    def get_language_name(self) -> str:
        """Get current language name"""
        return self.SUPPORTED_LANGUAGES.get(self.current_language, 'English')
    
    def translate(self, key: str, **kwargs) -> str:
        """
        Get translated text for a key
        
        Args:
            key: Translation key in dot notation (e.g., 'menu.file')
            **kwargs: Format arguments for the translation
        
        Returns:
            Translated text or key if translation not found
        """
        # Get translation for current language
        translation = self._get_nested_value(
            self.translations.get(self.current_language, {}),
            key
        )
        
        # Fallback to English if not found
        if translation is None and self.current_language != 'en':
            translation = self._get_nested_value(
                self.translations.get('en', {}),
                key
            )
        
        # Return key if still not found
        if translation is None:
            self.logger.warning(f"Translation not found: {key}")
            return key
        
        # Format with arguments if provided
        if kwargs:
            try:
                return translation.format(**kwargs)
            except KeyError as e:
                self.logger.warning(f"Missing format argument for {key}: {e}")
                return translation
        
        return translation
    
    def _get_nested_value(self, data: Dict, key: str) -> Any:
        """Get value from nested dictionary using dot notation"""
        keys = key.split('.')
        value = data
        
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
                if value is None:
                    return None
            else:
                return None
        
        return value
    
    def t(self, key: str, **kwargs) -> str:
        """Shorthand for translate()"""
        return self.translate(key, **kwargs)
    
    def get_available_languages(self) -> Dict[str, str]:
        """Get dictionary of available languages"""
        return self.SUPPORTED_LANGUAGES.copy()


# Global i18n instance
_i18n = None


def get_i18n() -> I18n:
    """Get global i18n instance"""
    global _i18n
    if _i18n is None:
        _i18n = I18n()
    return _i18n


def t(key: str, **kwargs) -> str:
    """Global translation function"""
    return get_i18n().translate(key, **kwargs)
