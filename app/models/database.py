from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Shared metadata; business models await actual dataset inspection."""
    pass
