
from sqlmodel import Field, SQLModel
class Config(SQLModel, table=True):
    __tablename__ ="Config_farm"
    ID: int=Field(primary_key =True)
    Key: str
    Value: str | None