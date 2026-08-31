from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.security.current import get_current_account
from app.db.database import get_session
from app.db.models import Account, ExperimentCreate, Experiment, ExperimentUpdate, Project, Dataset

router = APIRouter(
    prefix="/experiment",
    tags=["Experiment"]
)


# Create
@router.post("/create")
def create_experiment(
    data: ExperimentCreate,
    current_account: Account = Depends(get_current_account),
    session: Session = Depends(get_session)
):

    # Verify project
    existing_project = session.exec(
        select(Project).where(
            data.ProjectID == Project.ProjectID,
            Project.AccountID == current_account.AccountID
        )
    ).first()
    if not existing_project:
        raise HTTPException(status_code=409, detail="Not project found")
    
    # Verify dataset
    existing_dataset = session.exec(
        select(Dataset).where(
            data.DatasetID == Dataset.DatasetID,
            Dataset.AccountID == current_account.AccountID
        )
    ).first()
    if not existing_dataset:
        raise HTTPException(status_code=409, detail="Not dataset found")
    
    # Verify experiment name
    existing_experiment = session.exec(
        select(Experiment).join(
            Project, Experiment.ProjectID == Project.ProjectID
        ).where(
            Project.AccountID == current_account.AccountID,
            Experiment.Name == data.Name
        )
    ).first()
    if existing_experiment:
        raise HTTPException(status_code=409, detail="Repeated experiment name")
    
    experiment = Experiment.model_validate(
        data
    )
    
    # Save
    session.add(experiment)
    session.commit()
    session.refresh(experiment)
    
    return {"status": 200, "experiment id": experiment.ExperimentID}

# Read user's
@router.get("/read_all")
def get_all_experiments(
    current_account: Account = Depends(get_current_account),
    session: Session = Depends(get_session)
):
    experiments = session.exec(
        select(Experiment).join(
            Project, Experiment.ProjectID == Project.ProjectID
        ).where(
            Project.AccountID == current_account.AccountID
        )
    ).all()
    
    return {"state": 200, "experiments": experiments}

# Read One
@router.get("/read/{projectID}")
def get_experiment_with_id(
    experimentID: int,
    current_account: Account = Depends(get_current_account),
    session: Session = Depends(get_session)
):
    experiment = session.exec(
        select(Experiment).where(
            Experiment.ExperimentID == experimentID
        )
    ).first()
    
    if not experiment:
        raise HTTPException(status_code=404, detail="Experiment was not found")
    
    return {"state": 200, "experiment": experiment}

# Update
@router.put("/update/{experimentID}")
def update_experiment(
    data: ExperimentUpdate,
    current_account: Account = Depends(get_current_account),
    session: Session = Depends(get_session)
):
    experiment = session.exec(
        select(Experiment).join(
            Project, Experiment.ProjectID == Project.ProjectID
        ).where(
            Project.AccountID == current_account.AccountID,
            Experiment.ExperimentID == data.ExperimentID
        )
    ).first()

    if not experiment:
        raise HTTPException(status_code=404, detail="Wrong ID")
    
    experiment.Name = data.Name
    
    session.add(experiment)
    session.commit()
    session.refresh(experiment)
    
    return {"state": 200, "experiment": experiment}

# Delete
@router.delete("/delete/{experimentID}")
def delete_experiment(
    experimentID: int,
    current_account: Account = Depends(get_current_account),
    session: Session = Depends(get_session)
):
    experiment = session.exec( # JOIN
        select(Experiment).join(
            Project, Experiment.ProjectID == Project.ProjectID
        ).where(
            Project.AccountID == current_account.AccountID,
            Experiment.ExperimentID == experimentID
        )
    ).first()
    
    if not experiment:
        raise HTTPException(status_code=404, detail="Wrong ID or access denied")
    
    session.delete(experiment)
    session.commit()
    
    return {"state": 200, "detail": "Experiment deleted"}
