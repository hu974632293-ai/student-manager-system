import uvicorn

from app.main import app


if __name__ == "__main__":
    uvicorn.run("main:app", port=8088, host="127.0.0.1")
