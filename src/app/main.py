import uvicorn
from app.db.connection import init_db
from app.web.app import create_app

init_db()
app = create_app()

if __name__ == "__main__":
    # creates a server for each client
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)