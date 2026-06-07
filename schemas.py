from pydantic import BaseModel

class SerialCreate(BaseModel):

    line_id: int

    order_number: str

    serial_number: str

class StopCreate(BaseModel):

    line_id: int

    stop_minutes: int

class LoginRequest(BaseModel):

    username: str

    password: str

class OrderCodeCreate(BaseModel):

    order_code: str

    product_type: str