from environs import Env

env = Env()
env.read_env()

BOT_TOKEN: str = env.str('BOT_TOKEN', '')

MISTRAL_API_KEY = env.str("MISTRAL_API_KEY", "")
MISTRAL_MODEL = env.str("MISTRAL_MODEL", "")

CHUNK_SIZE = env.int("CHUNK_SIZE", )
DDG_REGION = env.str("DDG_REGION", "")
LANGUAGE_PROMPT = env.str("RU_LANG", "")


