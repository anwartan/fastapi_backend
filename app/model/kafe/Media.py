from sqlmodel import SQLModel, Field
import os

class Media(SQLModel,table=True):
    __tablename__="Media"
    ID:int = Field(default=None, primary_key=True)
    FileName:str
    FileType:str
    FileSize:int
    FilePath:str
    SubjectId:int
    SubjectType:str

    # def getUrl():
    #     APP_URL = os.getenv("APP_URL","")
    #     return APP_URL+"/media/kafe"
