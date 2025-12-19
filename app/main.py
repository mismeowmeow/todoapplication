from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
import hashlib
import binascii
from .send_mail import send_otp_email
from . import models
from .database import engine, SessionLocal
from .schema import UserCreate, UserResponse, UserLogin
from .schema import TaskCreate, TaskResponse, TaskUpdate
from typing import List
import secrets
from dotenv import load_dotenv
models.Base.metadata.create_all(bind=engine) 
load_dotenv()
app = FastAPI(
    title="Todo Application",
    description="A simple Todo application with user authentication and OTP verification.",
    version="1.0.0",
)

def hash_password(password: str) -> str:
    """Hash a password using PBKDF2-HMAC-SHA256 with a random salt.

    Returns: salt$hexderivedkey
    """
    salt = secrets.token_hex(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 100_000)
    return f"{salt}${binascii.hexlify(dk).decode()}"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a stored hash.
    
    Args:
        plain_password: The password to check.
        hashed_password: The stored hash in format salt$hexkey.
    
    Returns: True if password matches, False otherwise.
    """
    try:
        salt, stored_key = hashed_password.split("$")
        dk = hashlib.pbkdf2_hmac("sha256", plain_password.encode("utf-8"), salt.encode("utf-8"), 100_000)
        computed_key = binascii.hexlify(dk).decode()
        return computed_key == stored_key
    except (ValueError, Exception):
        return False


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Default FastAPI validation handling will be used (no custom handler)

@app.get("/")
def read_root():
    return {"message": "Welcome to my todo application!"}

@app.post("/register/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    # check duplicate email
    existing = db.query(models.User).filter(models.User.email == user.email).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

    # hash password using PBKDF2-HMAC-SHA256
    hashed_password = hash_password(user.password)

    db_user = models.User(
        first_name=user.first_name,
        last_name=user.last_name,
        email=user.email,
        password=hashed_password
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    # create OTP (secure random 6-digit string)
    code = str(secrets.randbelow(900000) + 100000)
    otp = models.Otp(
        user_id=db_user.id,
        otp_code=code
    )
    db.add(otp)
    db.commit()
    db.refresh(otp)

    send_otp_email(to_email=db_user.email, otp_code=code, first_name=db_user.first_name, last_name=db_user.last_name)
    # return the created user (response_model filters out password)
    return db_user


@app.post("/login", response_model=UserResponse)
def login(user: UserLogin, db: Session = Depends(get_db)):
    """Authenticate user with email and password. Returns user details if valid."""
    # Find user by email
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if not db_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    
    # Verify password
    if not verify_password(user.password, db_user.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    
    # Return user (password filtered out by response_model)
    return db_user


@app.post("/tasks/", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
def create_task(task: TaskCreate, db: Session = Depends(get_db)):
    db_task = models.Task(
        title=task.title,
        description=task.description,
        owner_id=task.owner_id,
        date=task.date,
        time=task.time,
        completed=task.completed
    )
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task

@app.get("/tasks/", response_model=List[TaskResponse])
def get_all_tasks(db: Session = Depends(get_db)):
    tasks = db.query(models.Task).all()
    return tasks


@app.get("/tasks/", response_model=List[TaskResponse])
def get_completed_tasks(db: Session = Depends(get_db)):
    """Return all tasks marked as completed."""
    tasks = db.query(models.Task).filter(models.Task.completed == True).all()
    return tasks

@app.get("/tasks/{task_id}", response_model=TaskResponse)
def get_task_by_id(task_id: int, db: Session = Depends(get_db)):
    task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return task



@app.put("/tasks/{task_id}", response_model=TaskResponse)
def update_task(task_id: int, task: TaskUpdate, db: Session = Depends(get_db)):
    db_task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if not db_task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    # Only update fields that were provided (avoid overwriting with None)
    if task.title is not None:
        db_task.title = task.title
    if task.description is not None:
        db_task.description = task.description
    if getattr(task, "date", None) is not None:
        db_task.date = task.date
    if getattr(task, "time", None) is not None:
        db_task.time = task.time
    if getattr(task, "completed", None) is not None:
        db_task.completed = task.completed
    
    db.commit()
    db.refresh(db_task)
    return db_task

@app.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(task_id: int, db: Session = Depends(get_db)):   
    db_task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if not db_task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    
    db.delete(db_task)
    db.commit()
    return

