from fastapi import FastAPI
from pydantic import BaseModel
from sqlalchemy import text
from fastapi.middleware.cors import CORSMiddleware

from database import engine

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class LoginRequest(BaseModel):
    email: str
    password: str


@app.post("/login")
def login(data: LoginRequest):

    with engine.connect() as conn:

        result = conn.execute(
            text(
                """
                SELECT *
                FROM users
                WHERE email = :email
                """
            ),
            {
                "email": data.email
            }
        )

        user = result.fetchone()

        if user is None:
            return {
                "success": False,
                "message": "User not found"
            }

        user = dict(user._mapping)

        if user["password"] != data.password:
            return {
                "success": False,
                "message": "Wrong password"
            }

        return {
            "success": True,
            "name": user["name"]
        }
    
@app.get("/user/{email}")
def get_user(email: str):

    with engine.connect() as conn:

        result = conn.execute(
            text("""
                SELECT *
                FROM users
                WHERE email = :email
            """),
            {"email": email}
        )

        user = result.fetchone()

        if not user:
            return {"error": "User not found"}

        return dict(user._mapping)
    
class SignupRequest(BaseModel):
    name: str
    age: int
    email: str
    password: str

@app.post("/signup")
def signup(data: SignupRequest):

    with engine.connect() as conn:

        conn.execute(
            text("""
                INSERT INTO users
                (name, age, email, password)
                VALUES
                (:name, :age, :email, :password)
            """),
            {
                "name": data.name,
                "age": data.age,
                "email": data.email,
                "password": data.password
            }
        )

        conn.commit()

    return {
        "success": True,
        "message": "Account Created Successfully"
    }