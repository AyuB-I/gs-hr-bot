from dataclasses import dataclass

from environs import Env
from sqlalchemy.engine.url import URL


@dataclass
class DbConfig:
    user: str
    password: str
    host: str
    port: int
    database: str
    pg_password: str

    # We provide a method to create a connection string easily.
    def construct_sqlalchemy_url(self, driver="asyncpg") -> URL:
        return URL.create(
            drivername=f"postgresql+{driver}",
            username=self.user,
            password=self.password,
            host=self.host,
            port=self.port,
            database=self.database
        )


@dataclass
class TgBot:
    token: str
    admin_ids: list[int]
    use_redis: bool


@dataclass
class Miscellaneous:
    other_params: str = None


@dataclass
class Config:
    tg_bot: TgBot
    db: DbConfig
    misc: Miscellaneous


def load_config(path: str = None):
    env = Env()
    env.read_env(path)

    return Config(
        tg_bot=TgBot(
            token=env.str("BOT_TOKEN"),
            admin_ids=list(map(int, env.list("ADMINS"))),
            use_redis=env.bool("USE_REDIS"),
        ),
        db=DbConfig(
            user=env.str('DB_USER'),
            password=env.str('DB_PASS'),
            host=env.str('DB_HOST'),
            port=env.int('DB_PORT'),
            database=env.str('DB_NAME'),
            pg_password=env.str('PG_PASS')
        ),
        misc=Miscellaneous()
    )
