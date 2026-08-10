from config import Configuration, get_config
from dotenv import load_dotenv
import os

load_dotenv(".env")


def test_config_vars_are_read_from_env():
    config = Configuration()

    assert isinstance(config.database_user, str)
    assert len(config.database_user) > 0
    assert config.database_host == os.environ.get("DATABASE_HOST")
    assert config.database_name == os.environ.get("DATABASE_NAME")
    assert config.database_pass == os.environ.get("DATABASE_PASS")
    assert config.database_user == os.environ.get("DATABASE_USER")


def test_get_config():
    config = get_config()
    assert isinstance(config, Configuration)

    assert config.database_user == os.environ.get("DATABASE_USER")

    os.environ['DATABASE_USER'] = "Peter"
    assert os.environ.get("DATABASE_USER") == "Peter"
    
    config = get_config()
    assert config.database_user == "Peter"
