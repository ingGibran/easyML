from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.security.current import get_current_account
from app.db.database import get_session
from app.db.models import Account, Project, ProjectCreate, ProjectRead, ProjectUpdate

router = APIRouter(
    prefix="/project",
    tags=["Project"]
)


# Create
@router.post("/create")
def create_project(
    data: ProjectCreate,
    current_account: Account = Depends(get_current_account),
    session: Session = Depends(get_session)
):

    # Verify project name
    existing_project = session.exec(
        select(Project).where(
            Project.AccountID == current_account.AccountID,
            Project.Name == data.Name
        )
    ).first()
    if existing_project:
        raise HTTPException(status_code=409, detail="Repeated project name")
    
    project = Project.model_validate(
        data,
        update={"AccountID": current_account.AccountID}
    )
    
    # Save
    session.add(project)
    session.commit()
    session.refresh(project)
    
    return {"status": 200, "project_id": project.ProjectID}

# Read user's
@router.get("/read_all")
def get_all_projects(
    current_account: Account = Depends(get_current_account),
    session: Session = Depends(get_session)
):
    projects = session.exec(
        select(Project).where(Project.AccountID == current_account.AccountID)
    ).all()
    
    return {"state": 200, "projects": projects if projects else []}

# Read One
@router.get("/read/{projectID}")
def get_project_with_id(
    projectID: int,
    current_account: Account = Depends(get_current_account),
    session: Session = Depends(get_session)
):
    project = session.exec(
        select(Project).where(
            (Project.AccountID == current_account.AccountID), (Project.ProjectID == projectID)    
        )
    ).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="Wrong ID")
    
    return {"state": 200, "project": project}

# Update
@router.put("/update/{projectID}")
def update_project(
    data: ProjectUpdate,
    current_account: Account = Depends(get_current_account),
    session: Session = Depends(get_session)
):
    project = session.exec(
        select(Project).where(
            (Project.AccountID == current_account.AccountID), (Project.ProjectID == data.ProjectID)    
        )
    ).first()

    if not project:
        raise HTTPException(status_code=404, detail="Wrong ID")
    
    project.Name = data.Name
    project.Description = data.Description
    
    session.add(project)
    session.commit()
    session.refresh(project)
    
    return {"state": 200, "project": project}

# Delete
@router.delete("/delete/{projectID}")
def delete_project(
    projectID: int,
    current_account: Account = Depends(get_current_account),
    session: Session = Depends(get_session)
):
    project = session.exec(
        select(Project).where(
            (Project.AccountID == current_account.AccountID), (Project.ProjectID == projectID)    
        )
    ).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="Wrong ID")
    
    session.delete(project)
    session.commit()
    
    return {"state": 200, "detail": "Project deleted"}
