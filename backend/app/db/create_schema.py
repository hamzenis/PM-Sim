from app.db.models import Base
from app.db.session import engine


def create_schema() -> None:
    """Create the development schema. Production changes will use Alembic migrations."""
    Base.metadata.create_all(engine)


if __name__ == "__main__":
    create_schema()
