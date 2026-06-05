from sqlmodel import SQLModel
from app.db.connection import engine
import app.db.model 

def init_db():
    SQLModel.metadata.create_all(engine)

if __name__ == '__main__':
    init_db()