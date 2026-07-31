from sqlmodel import SQLModel,Field


class Config(SQLModel,table=True):
    __tablename__="Config"
    ID:int = Field(primary_key=True)
    Key: str
    Value:str
