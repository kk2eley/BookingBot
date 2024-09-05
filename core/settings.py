from dataclasses import dataclass
from environs import Env


@dataclass
class Bot:
    bot_token: str
    admin_id: str


@dataclass
class Db:
    user: str
    host: str
    password: str
    db: str
    dsn: str
    echo: bool


@dataclass
class Settings:
    bot: Bot
    db: Db


def get_settings(path: str):
    env = Env()

    env.read_env(path)

    return Settings(
        bot=Bot(
            bot_token=env.str("BOT_TOKEN"),
            admin_id=env.str("ADMIN_ID")
        ),
        db=Db(
            user=env.str("DB_USER"),
            host=env.str("DB_HOST"),
            password=env.str("DB_PASSWORD"),
            db=env.str("DB_DATABASE"),
            dsn=f'postgresql+psycopg://{env.str("DB_USER")}:{env.str("DB_PASSWORD")}@{env.str("DB_HOST")}/{env.str("DB_DATABASE")}',
            echo=True if env("DB_ECHO") == 'True' else False,
        )
    )


settings = get_settings(".env")
print(settings)
