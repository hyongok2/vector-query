"""Configuration management utilities"""
import os
import json
import hashlib
from typing import Dict, Any, Optional
from abc import ABC, abstractmethod


class ConfigManagerInterface(ABC):
    """Abstract interface for configuration management"""

    @abstractmethod
    def save_settings(self, settings: Dict[str, Any]) -> bool:
        """Save settings to storage"""
        pass

    @abstractmethod
    def load_settings(self) -> Optional[Dict[str, Any]]:
        """Load settings from storage"""
        pass

    @abstractmethod
    def has_settings(self) -> bool:
        """Check if settings exist"""
        pass


class UserIdentifier:
    """User identification utilities"""

    @staticmethod
    def get_user_id(request_info: Optional[Dict[str, Any]] = None) -> str:
        """Get user identifier (IP-based hash for privacy)"""
        try:
            # In a real deployment, you might get this from Streamlit context
            # For now, we'll use a simple approach
            import streamlit as st

            # Try to get remote IP from Streamlit context
            if hasattr(st, 'context') and hasattr(st.context, 'headers'):
                headers = st.context.headers
                ip = headers.get('x-forwarded-for', headers.get('remote-addr', 'localhost'))
            else:
                ip = 'localhost'

            # Create hash for privacy
            return hashlib.sha256(ip.encode()).hexdigest()[:16]
        except Exception:
            return 'default_user'


class FileBasedConfigManager(ConfigManagerInterface):
    """File-based configuration manager"""

    def __init__(self, base_path: str = ".", user_identifier: Optional[str] = None):
        self.base_path = base_path
        self.user_identifier = user_identifier or UserIdentifier.get_user_id()

    def _get_settings_file_path(self) -> str:
        """Get settings file path for current user"""
        filename = f'user_settings_{self.user_identifier}.json'
        return os.path.join(self.base_path, filename)

    def save_settings(self, settings: Dict[str, Any]) -> bool:
        """Save settings to JSON file"""
        try:
            settings_file = self._get_settings_file_path()
            with open(settings_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"Failed to save settings: {e}")
            return False

    def load_settings(self) -> Optional[Dict[str, Any]]:
        """Load settings from JSON file"""
        try:
            settings_file = self._get_settings_file_path()
            if os.path.exists(settings_file):
                with open(settings_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Failed to load settings: {e}")
        return None

    def has_settings(self) -> bool:
        """Check if settings file exists"""
        settings_file = self._get_settings_file_path()
        return os.path.exists(settings_file)


class AppSettings:
    """Application settings container"""

    DEFAULT_SETTINGS = {
        'db_uri': '',
        'sql': 'SELECT * FROM EMSWO',
        'pk_col': 'id',
        'template_str': '{{title}} - {{description}}',
        'max_chars': 800,
        'strip_ws': True,
        'q_host': 'localhost',
        'q_port': 6333,
        'collection': 'my_collection',
        'batch_size': 64,
        'model': 'mE5-base',
        'preview_rows': 50,
        'max_rows': 0
    }

    def __init__(self, config_manager: ConfigManagerInterface):
        self.config_manager = config_manager
        self._settings = self._load_or_default()

    def _load_or_default(self) -> Dict[str, Any]:
        """Load settings or return defaults"""
        loaded_settings = self.config_manager.load_settings()
        if loaded_settings:
            # Merge with defaults to ensure all keys exist
            settings = self.DEFAULT_SETTINGS.copy()
            settings.update(loaded_settings)
            return settings
        return self.DEFAULT_SETTINGS.copy()

    def get(self, key: str, default: Any = None) -> Any:
        """Get setting value"""
        return self._settings.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Set setting value"""
        self._settings[key] = value

    def update(self, updates: Dict[str, Any]) -> None:
        """Update multiple settings"""
        self._settings.update(updates)

    def save(self) -> bool:
        """Save current settings"""
        return self.config_manager.save_settings(self._settings)

    def get_all(self) -> Dict[str, Any]:
        """Get all settings"""
        return self._settings.copy()

    def reset_to_defaults(self) -> None:
        """Reset all settings to defaults"""
        self._settings = self.DEFAULT_SETTINGS.copy()


class SettingsValidator:
    """Settings validation utilities"""

    @staticmethod
    def validate_db_uri(uri: str) -> bool:
        """Validate database URI format"""
        if not uri:
            return False

        valid_schemes = ['sqlite://', 'mysql://', 'postgresql://', 'oracle://']
        return any(uri.startswith(scheme) for scheme in valid_schemes)

    @staticmethod
    def validate_port(port: Any) -> bool:
        """Validate port number"""
        try:
            port_num = int(port)
            return 1 <= port_num <= 65535
        except (ValueError, TypeError):
            return False

    @staticmethod
    def validate_positive_int(value: Any) -> bool:
        """Validate positive integer"""
        try:
            num = int(value)
            return num > 0
        except (ValueError, TypeError):
            return False

    @staticmethod
    def validate_non_negative_int(value: Any) -> bool:
        """Validate non-negative integer"""
        try:
            num = int(value)
            return num >= 0
        except (ValueError, TypeError):
            return False


class ConfigManagerFactory:
    """Factory for creating configuration managers"""

    @staticmethod
    def create_file_manager(base_path: str = ".") -> ConfigManagerInterface:
        """Create file-based configuration manager"""
        return FileBasedConfigManager(base_path)

    @staticmethod
    def create_app_settings(config_manager: Optional[ConfigManagerInterface] = None) -> AppSettings:
        """Create application settings instance"""
        if config_manager is None:
            config_manager = ConfigManagerFactory.create_file_manager()
        return AppSettings(config_manager)