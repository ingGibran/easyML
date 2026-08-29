from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session, select
from datetime import timedelta

from app.db.database import get_session
from app.db.models import Account
from app.security.auth import verify_password, create_access_token
from app.security.auth import ACCESS_TOKEN_EXPIRE_MINUTES

router = APIRouter(
    prefix="/account",
    tags=["Account"]
    )

# Login
@router.post("/token")
def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(), 
    session: Session = Depends(get_session)
):
    # 1. Find account by Username
    account = session.exec(select(Account).where(Account.Username == form_data.username)).first()
    
    # 2. Verify existence and password match
    if not account or not verify_password(form_data.password, account.Hashed_Password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 3. Generate token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": account.Username}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}


# Register
router.post("/register")
def register():
    
    """
    @app.get("/accounts/me", response_model=Account)
def read_accounts_me(current_account: Account = Depends(get_current_account)):
    # current_account contains the fully loaded SQLModel instance
    return current_account
    
@app.get("/projects")
def get_my_projects(current_account: Account = Depends(get_current_account)):
    # You can now safely access relationships
    return current_account.projects
    """