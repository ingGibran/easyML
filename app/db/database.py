from sqlmodel import Session, SQLModel, create_engine 

from app.core.config import settings 

engine = create_engine(
    settings.database_url,
    echo=True,
)


"""
Get session | Dependency Injection
"""
def get_session():
    with Session(engine) as session:
        yield session