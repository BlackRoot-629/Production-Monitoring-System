from fastapi import FastAPI

from database import engine
from models import Base

from database import SessionLocal
from models import Serial, OrderCode
from schemas import SerialCreate

from sqlalchemy import func

from schemas import StopCreate
from models import LineStop
from models import SwitchLog
from services import calculate_expected_count
from models import User
from schemas import LoginRequest
from schemas import OrderCodeCreate

from pydantic import BaseModel

from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi import Request


from fastapi.templating import Jinja2Templates

Base.metadata.create_all(bind=engine)

app = FastAPI()


templates = Jinja2Templates(
    directory="templates"
)


@app.get("/line/{line_id}")
def scan_page(
    request: Request,
    line_id: int
):

    return templates.TemplateResponse(
        request=request,
        name="scan.html",
        context={
            "line_id": line_id
        }
    )

@app.post("/api/serial")
def create_serial(data: SerialCreate):

    db = SessionLocal()

    try:

        order_code = data.order_number.split("-")[1]

        product = db.query(OrderCode).filter(
            OrderCode.order_code == order_code
        ).first()

        if not product:

            return {
                "error": "Order Code Not Found"
            }

        existing = db.query(Serial).filter(
            Serial.serial_number == data.serial_number
        ).first()

        if existing:

            return {
                "error": "Duplicate Serial"
            }
        serial = Serial(

            line_id=data.line_id,

            serial_number=data.serial_number,

            order_number=data.order_number,

            order_code=order_code,

            product_type=product.product_type

        )

        db.add(serial)

        db.commit()

        return {
            "message": "Saved"
        }

    except Exception as ex:

        db.rollback()

        return {
            "error": str(ex)
        }

    finally:

        db.close()

@app.get("/monitor/{line_id}")
def monitor(
    request: Request,
    line_id: int
):

    return templates.TemplateResponse(
        request=request,
        name="monitor.html",
        context={
            "line_id": line_id
        }
    )

@app.get("/api/monitor/{line_id}")
def get_monitor(line_id: int):

    db = SessionLocal()

    try:
        stop_minutes = db.query(
        func.coalesce(
            func.sum(LineStop.stop_minutes),
            0
        )
        ).filter(
            LineStop.line_id == line_id
        ).scalar()

        switch_count = db.query(
            func.count()
        ).filter(
            SwitchLog.line_id == line_id
        ).scalar()

        expected_count = calculate_expected_count(
            stop_minutes,
            switch_count
        )



        aio = db.query(func.count()).filter(
            Serial.line_id == line_id,
            Serial.product_type == "AIO"
        ).scalar()

        mnt = db.query(func.count()).filter(
            Serial.line_id == line_id,
            Serial.product_type == "MNT"
        ).scalar()

        case = db.query(func.count()).filter(
            Serial.line_id == line_id,
            Serial.product_type == "CASE"
        ).scalar()

        nb = db.query(func.count()).filter(
            Serial.line_id == line_id,
            Serial.product_type == "NB"
        ).scalar()

        actual_count = db.query(func.count()).filter(
            Serial.line_id == line_id
        ).scalar()

        aio_equivalent = (

            aio

            + (mnt * 0.60)

            + (case * 0.80)

            + nb

        )

        difference = actual_count - expected_count

        production_score = actual_count
        return {

            "aio": aio,

            "mnt": mnt,

            "case": case,

            "nb": nb,

            "aio_equivalent": int(aio_equivalent),
            
            "actual_count": actual_count,

            "expected_count": expected_count,

            "difference": difference,

            "stop_minutes": stop_minutes,

            "switch_count": switch_count,

            "production_score": production_score

        }

    finally:

        db.close()

@app.post("/api/stop")
def add_stop(data: StopCreate):

    db = SessionLocal()

    try:

        stop = LineStop(

            line_id=data.line_id,

            stop_minutes=data.stop_minutes

        )

        db.add(stop)

        db.commit()

        return {
            "message": "Stop Saved"
        }

    finally:

        db.close()

@app.post("/api/switch/{line_id}")
def use_switch(line_id: int):

    db = SessionLocal()

    try:

        count = db.query(func.count()).filter(
            SwitchLog.line_id == line_id
        ).scalar()

        if count >= 2:

            return {
                "error": "Maximum usage reached"
            }

        switch = SwitchLog(

            line_id=line_id

        )

        db.add(switch)

        db.commit()

        return {
            "message": "Switch Saved"
        }

    finally:

        db.close()

@app.get("/")
def login_page(request: Request):

    return templates.TemplateResponse(
        request=request,
        name="login.html",

        context={
            "request": request
        }

    )

@app.post("/api/login")
def login(data: LoginRequest):

    db = SessionLocal()

    try:

        user = db.query(User).filter(

            User.username == data.username,

            User.password == data.password

        ).first()

        if not user:

            return {
                "error":
                "Invalid Username Or Password"
            }

        return {

            "username":
            user.username,

            "role":
            user.role,

            "line_id":
            user.line_id

        }

    finally:

        db.close()


@app.get("/dashboard")
def dashboard(
    request: Request
):

    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",

        context={
            "request": request
        }
    )


@app.get("/api/dashboard")
def dashboard_data():

    db = SessionLocal()

    try:

        result = []

        for line_id in range(1,7):

            actual_count = db.query(
                func.count()
            ).filter(
                Serial.line_id == line_id
            ).scalar()

            aio = db.query(func.count()).filter(
                Serial.line_id == line_id,
                Serial.product_type == "AIO"
            ).scalar()

            mnt = db.query(func.count()).filter(
                Serial.line_id == line_id,
                Serial.product_type == "MNT"
            ).scalar()

            case = db.query(func.count()).filter(
                Serial.line_id == line_id,
                Serial.product_type == "CASE"
            ).scalar()

            nb = db.query(func.count()).filter(
                Serial.line_id == line_id,
                Serial.product_type == "NB"
            ).scalar()

            aio_equivalent = (

                aio

                + (mnt * 0.60)

                + (case * 0.80)

                + nb

            )

            stop_minutes = db.query(
                func.coalesce(
                    func.sum(
                        LineStop.stop_minutes
                    ),
                    0
                )
            ).filter(
                LineStop.line_id == line_id
            ).scalar()

            switch_count = db.query(
                func.count()
            ).filter(
                SwitchLog.line_id == line_id
            ).scalar()

            expected_count = calculate_expected_count(
                stop_minutes,
                switch_count
            )

            difference = (
                actual_count -
                expected_count
            )

            result.append({

                "line_id":
                line_id,

                "actual":
                actual_count,

                "aio_equivalent":
                int(aio_equivalent),

                "expected":
                expected_count,

                "difference":
                difference

            })

        return result

    finally:

        db.close()

@app.get("/ordercode")
def ordercode_page(
    request: Request
):

    return templates.TemplateResponse(
        request=request,
        name="ordercode.html",
        context={
            "request": request
        }

    )

@app.post("/api/ordercode")
def add_ordercode(data: OrderCodeCreate):

    db = SessionLocal()

    try:

        existing = db.query(
            OrderCode
        ).filter(
            OrderCode.order_code ==
            data.order_code
        ).first()

        if existing:

            return {
                "error":
                "Order Code Exists"
            }

        item = OrderCode(

            order_code=data.order_code,

            product_type=data.product_type

        )

        db.add(item)

        db.commit()

        return {
            "message":
            "Saved"
        }

    finally:

        db.close()