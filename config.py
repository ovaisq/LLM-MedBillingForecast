# config.py
# ©2024, Ovais Quraishi

import configparser
import os
from pathlib import Path

CONFIG_FILE = 'setup.config'


class ConfigError(Exception):
    """Custom exception for configuration errors."""
    pass


def read_config(file_path):
    """Read setup config file"""
    if Path(str(Path(file_path).resolve())).exists():
        config_obj = configparser.RawConfigParser()
        config_obj.read(file_path)
        return config_obj
    raise FileNotFoundError(f"Config file {file_path} not found.")


def get_config():
    """Returns the parsed configuration object"""
    return read_config(CONFIG_FILE)


# Provide default values when config file is not available
def get_config_with_defaults():
    """Returns configuration with defaults from environment or file."""
    try:
        return get_config()
    except FileNotFoundError:
        # Return a minimal config object for imports to work
        config = configparser.RawConfigParser()
        config.add_section('psqldb')
        config.add_section('service')
        config.set('service', 'JWT_SECRET_KEY', os.environ.get('JWT_SECRET_KEY', 'default-secret-key'))
        config.set('service', 'APP_SECRET_KEY', os.environ.get('APP_SECRET_KEY', 'default-app-key'))
        config.set('service', 'IDENTITY', os.environ.get('IDENTITY', 'billing-gpt'))
        config.set('service', 'SRVC_SHARED_SECRET', os.environ.get('SRVC_SHARED_SECRET', 'default-secret'))
        config.set('service', 'OLLAMA_API_URL', os.environ.get('OLLAMA_API_URL', 'http://localhost:11434'))
        config.set('service', 'ENCRYPTION_KEY', os.environ.get('ENCRYPTION_KEY', 'encryption.key'))
        config.set('service', 'PATIENT_DATA_ENCRYPTION_ENABLED', os.environ.get('PATIENT_DATA_ENCRYPTION_ENABLED', 'true'))
        config.set('service', 'LLMS', os.environ.get('LLMS', 'llama3.2'))
        config.set('service', 'MEDLLMS', os.environ.get('MEDLLMS', 'medllama2'))
        config.set('service', 'ENDPOINT_URL', os.environ.get('ENDPOINT_URL', 'http://localhost:5000'))
        return config
