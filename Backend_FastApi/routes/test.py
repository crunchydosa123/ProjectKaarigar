# test.py
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()

# Define your Pydantic model
class Item(BaseModel):
    name: str
    description: str | None = None

# Define your route
@router.post("/items/")
def create_item(item: Item):
    return {"message": f"Item '{item.name}' created", "desc": item.description}

@router.get("/test")
def read_test():
    return {"message": "This is a test route"}