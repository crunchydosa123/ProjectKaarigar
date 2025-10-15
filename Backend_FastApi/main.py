#pip install "fastapi[standard]" <- to install all the standard dependencies in fastapi

from typing import Union
from fastapi import FastAPI

from routes import test

app = FastAPI()

app.include_router(test.router , prefix="/testing")

@app.get("/")
def read_root():
    return {"Status": "API is running"}

