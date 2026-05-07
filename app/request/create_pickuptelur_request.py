from pydantic import BaseModel, field_validator

from app.request.pickuptelur_request import Pickuptelurrequest

class Createpickuptelurrequest(BaseModel):
    data: list[Pickuptelurrequest]

    @field_validator("data")
    def data_must_not_empty(cls, v):
        if not v:
            raise ValueError(
                "data must be not empty"
            )
        return v


