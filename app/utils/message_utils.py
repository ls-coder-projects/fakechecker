from pathlib import Path

import yaml


def load_messages():
    """Загрузчик сообщений из yaml"""
    config_path = Path(__file__).parent.parent / 'config' / 'messages.yaml'
    with open(config_path, 'r', encoding='utf-8') as file:
        return yaml.safe_load(file)


messages = load_messages()
