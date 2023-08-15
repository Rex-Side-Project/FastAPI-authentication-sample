from fastapi import APIRouter, Depends, HTTPException, status
import configparser
from datetime import datetime, timedelta
from typing import Optional
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from passlib.context import CryptContext
from jose import JWTError, jwt
from database import get_db, engine
from sqlalchemy.orm import Session
from sqlalchemy import select
from database import User as UserInDB
from pprint import pprint

config = configparser.ConfigParser()
config.read('config.ini')

router = APIRouter()

SECRET_KEY = config['app']['SECRET_KEY']
ALGORITHM = config['app']['ALGORITHM']
ACCESS_TOKEN_EXPIRE_MINUTES = config['app']['ACCESS_TOKEN_EXPIRE_MINUTES']

pwd_content = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


class User(BaseModel):
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    disabled: Optional[bool] = None


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    user_name: str = None


def verify_password(plain_password, hashed_password):
    return pwd_content.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_content.hash(password)


def get_user(db: Session, username: str) -> UserInDB:
    user = db.query(UserInDB).filter(UserInDB.username == username).first()
    return user


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta if expires_delta else timedelta(minutes=15))

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


@router.post("/token", response_model=Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = get_user(db, form_data.username)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(
        minutes=float(ACCESS_TOKEN_EXPIRE_MINUTES))
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")

        if username is None:
            raise credentials_exception

        token_data = TokenData(user_name=username)
    except JWTError:
        raise credentials_exception

    user = get_user(db, username=token_data.user_name)

    if user is None:
        raise credentials_exception

    return user


@router.get("/users/me", response_model=User)
def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user


class UserRegist(User):
    password: str


@router.post("/users/regist", response_model=User)
def create_user(user: UserRegist, db: Session = Depends(get_db)):
    db_user = UserInDB(username=user.username,
                       email=user.email,
                       full_name=user.full_name,
                       hashed_password=get_password_hash(user.password))

    db.add(db_user)
    db.commit()

    userInDB = get_user(db, user.username)
    return userInDB

    return db_user


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[str] = None
    password: Optional[str] = None

    def to_update_dict(self) -> dict:
        update_data = {
            'full_name': self.full_name,
            'email': self.email,
            'hashed_password': get_password_hash(self.password) if self.password else None
        }
        return {k: v for k, v in update_data.items() if v is not None}


@router.put("/user/info", response_model=User)
def update_user(user: UserUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # 移除值為 None 的鍵
    update_user_data = user.to_update_dict()

    db.query(UserInDB).filter(UserInDB.username ==
                              current_user.username).update(update_user_data)
    db.commit()
    return current_user


@router.delete("/user", response_model=User)
def delete_user(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    db.query(UserInDB).filter(UserInDB.username ==
                              current_user.username).delete()
    db.commit()
    return current_user
