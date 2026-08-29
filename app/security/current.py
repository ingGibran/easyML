from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlmodel import Session, select
import jwt

from .auth import SECRET_KEY, ALGORITHM
from app.db.models import Account
from app.db.database import get_session


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/account/token")

def get_current_account(token: str = Depends(oauth2_scheme), session: Session = Depends(get_session)):
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
    except jwt.InvalidTokenError:
        raise credentials_exception
    
    # Query your SQLModel Account table
    account = session.exec( select(Account).where(Account.Username == username) ).first()
    if account is None:
        raise credentials_exception
        
    return account