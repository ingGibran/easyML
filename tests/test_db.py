from sqlmodel import text 

from app.db.database import engine

def test_db_connection():
    with engine.connect() as connection:
        result = connection.exec_driver_sql("SELECT 1")
        
        assert result.scalar() == 1 