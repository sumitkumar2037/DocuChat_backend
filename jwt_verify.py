import jwt
from fastapi import Depends, HTTPException, Header
from dotenv import load_dotenv
import os
from session_management import cleanup_guest_session
import uuid
from datetime import datetime, timedelta
load_dotenv()
#create jwt with secrect key
SECRET_KEY = os.getenv("JWT_SECRET")
JWT_ALGO = "HS256"
JWT_EXP_MINUTES = 5

def create_guest_jwt(guest_id: str):
    payload = {
        "sub": guest_id,
        "iat": datetime.utcnow(),
        "exp": datetime.utcnow() + timedelta(minutes=JWT_EXP_MINUTES),
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm=JWT_ALGO)
    return token

def verify_jwt(authorization: str = Header(...)):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid auth header")

    token = authorization.split(" ")[1]

    try:
        
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[JWT_ALGO]
        )
        print('guest_id',payload["sub"])
        return payload["sub"]

    except jwt.ExpiredSignatureError:
        print('token expire')
        try:
            payload = jwt.decode(
                token,
                SECRET_KEY,
                algorithms=[JWT_ALGO],
                options={"verify_exp": False}
            )
            guest_id = payload.get("sub")
            print('token expired for guest_id ',guest_id)
            if guest_id:
                cleanup_guest_session(guest_id)
        except jwt.InvalidTokenError:
            pass  # nothing to clean

        raise HTTPException(status_code=401, detail="Session expired")

    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
