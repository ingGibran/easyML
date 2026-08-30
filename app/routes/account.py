from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session, select
from datetime import timedelta

from app.db.database import get_session
from app.db.models import Account, AccountCreate
from app.security.auth import verify_password, create_access_token, get_password_hash
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
    account = session.exec(
        select(Account).where(
            (Account.Username == form_data.username) | (Account.Email == form_data.username)
            )
    ).first()
    
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
@router.post("/register")
def register(
    data: AccountCreate,
    session: Session = Depends(get_session)
    ):
    
    # Verify personal information
    if not data.Phone.isdigit():
        raise HTTPException(status_code=400, detail="Wrong Information")
    
    if session.exec( select(Account).where(Account.Username == data.Username) ).first():
        raise HTTPException(status_code=409, detail="Username in use")
    
    if session.exec( select(Account).where(Account.Email == data.Email) ).first():
        raise HTTPException(status_code=409, detail="Email in use")
        
    if session.exec( select(Account).where(Account.Phone == data.Phone) ).first():
        raise HTTPException(status_code=409, detail="Phone in use")
    
    # Save
    hashed_password = get_password_hash(data.Password)
    account = Account.model_validate(
        data,
        update={"Hashed_Password": hashed_password}
    )
    
    # Commit
    session.add(account)
    session.commit()
    session.refresh(account)
    
    return {"state:": "200", "account_id": account.AccountID}
    


    
    

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