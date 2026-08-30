from sqlmodel import Field, SQLModel, Relationship
from datetime import datetime, date
from typing import Optional

"""
ORM Models
"""

# Account
class AccountBase(SQLModel):
    Username: str = Field(max_length=50, unique=True)
    Email: str = Field(max_length=50, unique=True)
    Phone: str = Field(max_length=10, unique=True)
    Birthdate: date
    Occupation: str = Field(max_length=50)

class AccountCreate(AccountBase):
    Password: str = Field(max_length=100)

class AccountRead(AccountBase):
    AccountID: int

class Account(AccountBase, table=True): 
    AccountID: int | None = Field(default=None, primary_key=True)
    
    Hashed_Password: str = Field(min_length=8, max_length=72)
    
    rate: Optional["Rate"] = Relationship(back_populates="account")
    projects: list["Project"] = Relationship(back_populates="account")

# Rate
class Rate (SQLModel, table=True):
    RateID: int | None = Field(default=None, primary_key=True)
    
    AccountID: int = Field(foreign_key="account.AccountID")
    
    Stars_Number: int = Field(ge=0, le=5)
    Comment: str = Field(max_length=100)

    account: Account = Relationship(back_populates="rate")

# Project
class ProjectBase(SQLModel):
    Name: str = Field(max_length=50)
    Description: str

class ProjectCreate(ProjectBase):
    pass

class ProjectRead(ProjectBase):
    ProjectID: int
    AccountID: int 
    Created_At: datetime

class Project(ProjectBase, table=True):
    ProjectID: int | None = Field(default=None, primary_key=True)
    
    AccountID: int = Field(foreign_key="account.AccountID")

    Created_At: datetime = Field(default_factory=datetime.now)

    account: Account = Relationship(back_populates="projects")
    experiments: list["Experiment"] = Relationship(back_populates="project")

# Dataset
class Dataset(SQLModel, table=True):
    DatasetID: int | None = Field(default=None, primary_key=True)
    
    Name: str = Field(max_length=50)
    Description: str
    File_Path: str 
    File_Format: str = Field(max_length=10)
    Uploaded_Date: datetime = Field(default_factory=datetime.now)
    Last_Save_Date: datetime = Field(default_factory=datetime.now)    

    experiments: list["Experiment"] = Relationship(back_populates="dataset")

# Experiment
class Experiment(SQLModel, table=True):
    ExperimentID: int | None = Field(default=None, primary_key=True)
    
    ProjectID: int = Field(foreign_key="project.ProjectID")
    DatasetID: int = Field(foreign_key="dataset.DatasetID")
    
    Name: str = Field(max_length=50)
    Created_At: datetime = Field(default_factory=datetime.now)

    project: Project = Relationship(back_populates="experiments")
    dataset: Dataset = Relationship(back_populates="experiments")
    models: list["Model"] = Relationship(back_populates="experiment")

# Model
class Model(SQLModel, table=True):
    ModelID: int | None = Field(default=None, primary_key=True)
    
    ExperimentID: int = Field(foreign_key="experiment.ExperimentID")
    
    Name: str = Field(max_length=50)
    Version: str = Field(max_length=50)
    Status: str = Field(max_length=50)
    Framework: str = Field(max_length=50)
    File_Path: str 
    File_Format: str = Field(max_length=10)
    
    experiment: Experiment = Relationship(back_populates="models")
    tests: list["Test"] = Relationship(back_populates="model")
    model_metric_logs: list["Model_Metric_Log"] = Relationship(back_populates="model")
    deploys: list["Deploy"] = Relationship(back_populates="model")
    inference_logs: list["Inference_Log"] = Relationship(back_populates="model")

# Test
class Test(SQLModel, table=True):
    TestID: int | None = Field(default=None, primary_key=True)
    
    ModelID: int = Field(foreign_key="model.ModelID")
    
    Accuracy: float
    Precision: float 
    Recall: float 
    F1: float 
    Final_Train_Loss: float 
    Final_Eval_Loss: float 
    Mean_Train_Loss: float 
    Mean_Eval_Loss: float 
    Made_At: datetime = Field(default_factory=datetime)

    model: Model = Relationship(back_populates="tests")

# Model_Metric_Log
class Model_Metric_Log(SQLModel, table=True):
    Model_Metric_LogID: int | None = Field(default=None, primary_key=True)
    
    ModelID: int = Field(foreign_key="model.ModelID")
    Epoch: int 
    Step: int 
    Train_Loss: float 
    Eval_Loss: float 

    model: Model = Relationship(back_populates="model_metric_logs")

# Deploy
class Deploy(SQLModel, table=True):
    DeployID: int | None = Field(default=None, primary_key=True)
    
    ModelID: int = Field(foreign_key="model.ModelID") 
    API_URL: str
    # API_KEY: str
    
    model: Model = Relationship(back_populates="deploys")

# Inference_Log
class Inference_Log(SQLModel, table=True):
    Inference_LogID: int | None = Field(default=None, primary_key=True)
    
    ModelID: int = Field(foreign_key="model.ModelID")
    Info: str 
    Made_At: datetime = Field(default_factory=datetime.now)
    
    model: Model = Relationship(back_populates="inference_logs")