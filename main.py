import uvicorn
from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware
from starlette.responses import JSONResponse, RedirectResponse
from starlette.requests import Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, Integer, String, VARCHAR
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from pydantic import BaseModel

app = FastAPI()

origins = [
    "http://localhost.tiangolo.com",
    "https://localhost.tiangolo.com",
    "http://localhost",
    "http://localhost:8080",
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

app.add_middleware(SessionMiddleware, secret_key="mhmm")
engine = create_engine("mysql+mysqlconnector://root@localhost:3306/todo")
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Item(Base):
    __tablename__ = "items"

    id = Column(Integer, primary_key=True, index=True)
    data = Column(String(230))

class Items(BaseModel):
    data: str

class ItemCreate(Items):
    pass

Base.metadata.create_all(bind=engine)

@app.get("/get-todo")
def get_todo():
    db = SessionLocal()
    items = db.query(Item).all()
    db.close()
    return items

@app.post("/add")
def add_item(data: Items):
    db = SessionLocal()
    item = Item(data=data.data)
    db.add(item)
    db.commit()
    db.refresh(item)
    db.close()
    return item

@app.put("/update/{item_id}")
def update_item(item_id: int, data: Items):
    db = SessionLocal()
    item = db.query(Item).get(item_id)
    if item:
        item.data = data.data
        db.commit()
        db.refresh(item)
        db.close()
        return item
    db.close()
    return {"error": "Item not found"}

@app.delete("/delete/{item_id}")
def delete_item(item_id: int):
    db = SessionLocal()
    item = db.query(Item).get(item_id)
    if item:
        db.delete(item)
        db.commit()
        db.close()
        return {"message": "Item deleted"}
    db.close()
    return {"error": "Item not found"}

class UserBase(BaseModel):
    email: str
    password: str

class User(Base):
    __tablename__ = "users"

    email = Column(String(100), primary_key=True)
    password = Column(String(100))

@app.post("/login")
def login(user: UserBase, request: Request):
    db = SessionLocal()
    user = db.query(User).filter_by(email=user.email, password=user.password).first()
    db.close()
    if user:
        session = request.session
        session["user"] = user.email
        session["password"] = user.password

        return {"message": "Login successful"}
    return {"error": "Invalid credentials"}

@app.post("/register")
def register(creds: UserBase, request: Request):
    db = SessionLocal()
    user = db.query(User).filter_by(email=creds.email).first()
    if user:
        db.close()
        return {"error": "User already exists"}
    new_user = User(email=creds.email, password=creds.password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    db.close()

    session = request.session
    session["user"] = new_user.email
    session["password"] = new_user.password

    return {"message": "Registration successful"}

@app.get("/get-users")
def get_users():
    db = SessionLocal()
    users = db.query(User).all()
    db.close()
    return users

@app.get("/get-user-using-cookie")
def get_user(request: Request):
    session = request.session
    if session.get("user"):
        return {
                "user": session["user"],
                "password": session["password"]
                }
    return {"error": "User not logged in"}

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8080)
