from pydantic import BaseModel, field_validator


class BiometricRequest(BaseModel):
    device_id:str
    token_biometric:str
    @field_validator('device_id')
    def validate_Device_id(cls, value):
        if not value:
            raise ValueError('Device_id must not be empty')
        return value
    