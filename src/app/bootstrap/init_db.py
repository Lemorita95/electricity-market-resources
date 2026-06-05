from sqlmodel import SQLModel
from app.db.connection import admin_engine
import app.db.model 

def init_db():
    SQLModel.metadata.create_all(admin_engine)

if __name__ == '__main__':
    init_db()