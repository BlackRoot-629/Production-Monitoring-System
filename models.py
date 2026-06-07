from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import Column, Integer, String
from sqlalchemy import DateTime
from datetime import datetime
from sqlalchemy import ForeignKey
from sqlalchemy import DateTime
from datetime import datetime

class Base(DeclarativeBase):
    pass


class Line(Base):

    __tablename__ = "lines"

    id = Column(Integer, primary_key=True)

    name = Column(String)

class OrderCode(Base):

    __tablename__ = "order_codes"

    id = Column(Integer, primary_key=True)

    order_code = Column(String(10), unique=True)

    product_type = Column(String(20))   

class Serial(Base):

    __tablename__ = "serials"

    id = Column(Integer, primary_key=True)

    line_id = Column(Integer, ForeignKey("lines.id"))

    serial_number = Column(String(100), unique=True)

    order_number = Column(String(50))

    order_code = Column(String(10))

    product_type = Column(String(20))

    created_at = Column(DateTime, default=datetime.utcnow)

class LineStop(Base):

    __tablename__ = "line_stops"

    id = Column(Integer, primary_key=True)

    line_id = Column(Integer, ForeignKey("lines.id"))

    stop_minutes = Column(Integer)

    created_at = Column(DateTime, default=datetime.utcnow)

class SwitchLog(Base):

    __tablename__ = "switch_logs"

    id = Column(Integer, primary_key=True)

    line_id = Column(Integer, ForeignKey("lines.id"))

    created_at = Column(DateTime, default=datetime.utcnow)

class User(Base):

    __tablename__ = "users"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    username = Column(
        String,
        unique=True
    )

    password = Column(
        String
    )

    role = Column(
        String
    )

    line_id = Column(
        Integer,
        nullable=True
    )