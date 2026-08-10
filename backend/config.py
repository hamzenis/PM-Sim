from typing import Optional

from dotenv import load_dotenv
from pydantic import BaseSettings

load_dotenv(".env")


class Configuration(BaseSettings):
    """Configuration Management class. This class reads the environment
    variables required for the database connection vom the environment.

    Args:
        No arguments need to be passed to initialize an object of the
        class since it reads the env vars automatically.
    """

    database_name: str
    database_host: str
    database_port: Optional[str]
    database_user: str
    database_pass: str
    server: Optional[int] = 0
    logging_level: Optional[str] = "INFO"


def get_config() -> Configuration:
    """This function should be used to create a Configuration object.
    A configuration object stores the legacy relational database settings.

    Returns:
        Configuration: Instance of Configuration class
    """
    load_dotenv("backend/.env")
    return Configuration()
