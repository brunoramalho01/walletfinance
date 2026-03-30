# -*- coding: utf-8 -*-
"""Application configuration.

Most configuration is set via environment variables.

For local development, use a .env file to set
environment variables.
"""
from pathlib import Path
from environs import Env

BASE_DIR = Path(__file__).resolve().parent.parent

env = Env()
env.read_env()
# Fiz uma edição aqui para que ele consiga ler o caminho do banco de dados sqlite mesmo que seja relativo, ou seja, sem a necessidade de colocar o caminho absoluto. Assim, ele vai funcionar tanto no ambiente de desenvolvimento quanto em produção, onde o caminho pode ser diferente.
ENV = env.str("FLASK_ENV", default="production")
DEBUG = ENV == "development"
# Configuração do banco de dados
# O código abaixo ajusta o caminho do banco de dados SQLite para ser relativo ao diretório do projeto, garantindo que funcione tanto em desenvolvimento quanto em produção.
_database_url = env.str("DATABASE_URL")
if _database_url.startswith("sqlite:///"):
    sqlite_path = _database_url[len("sqlite:///"):].lstrip("/\\")
    if not Path(sqlite_path).is_absolute():
        _database_url = f"sqlite:///{(BASE_DIR / sqlite_path).as_posix()}"
SQLALCHEMY_DATABASE_URI = _database_url
SECRET_KEY = env.str("SECRET_KEY")
SEND_FILE_MAX_AGE_DEFAULT = env.int("SEND_FILE_MAX_AGE_DEFAULT")
BCRYPT_LOG_ROUNDS = env.int("BCRYPT_LOG_ROUNDS", default=13)
DEBUG_TB_ENABLED = DEBUG
DEBUG_TB_INTERCEPT_REDIRECTS = False
CACHE_TYPE = (
    "flask_caching.backends.SimpleCache"  # Can be "MemcachedCache", "RedisCache", etc.
)
SQLALCHEMY_TRACK_MODIFICATIONS = False
