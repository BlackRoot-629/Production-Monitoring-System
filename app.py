from fastapi import FastAPI

from database import engine
from models import Base

from database import SessionLocal
from models import Serial, OrderCode
from schemas import SerialCreate

from sqlalchemy import func, or_

from schemas import StopCreate
from models import LineStop
from models import SwitchLog
from services import calculate_expected_count
from models import User
from schemas import LoginRequest
from schemas import OrderCodeCreate
from schemas import UserCreate, UserUpdate
from schemas import SerialUpdate

from pydantic import BaseModel

import jdatetime
from fastapi.responses import FileResponse
from export_all_excel import export_all_production
from export_excel import export_production

from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi import Request
from fastapi import Query

from datetime import datetime

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
def update_serial(
    serial_id:int,
    data:SerialUpdate
):

    db=SessionLocal()

    try:

        serial=db.query(Serial).filter(
            Serial.id==serial_id
        ).first()

        if not serial:

            return {"error":"Not Found"}

        serial.order_number=data.order_number

        serial.serial_number=data.serial_number

        db.commit()

        return {"message":"Updated"}

    finally:

        db.close()
def get_serial(serial_id:int):

    db = SessionLocal()

    try:

        serial = (

            db.query(Serial)

            .filter(
                Serial.id == serial_id
            )

            .first()

        )

        if not serial:

            return {

                "error":"Serial Not Found"

            }

        return {

            "id":serial.id,

            "order_number":serial.order_number,

            "serial_number":serial.serial_number,

            "line_id":serial.line_id,

            "time":serial.created_at.strftime("%Y/%m/%d %H:%M")

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
    today = datetime.now().replace(

    hour=0,

    minute=0,

    second=0,

    microsecond=0

    )

    db = SessionLocal()

    try:
        stop_minutes = db.query(
        func.coalesce(
            func.sum(LineStop.stop_minutes),
            0
        )
        ).filter(
            LineStop.line_id == line_id,
            LineStop.created_at >= today
        ).scalar()

        switch_count = db.query(
            func.count()
        ).filter(
            SwitchLog.line_id == line_id,
            SwitchLog.created_at >= today
        ).scalar()

        expected_count = calculate_expected_count(
            stop_minutes,
            switch_count
        )



        aio = db.query(func.count()).filter(
            Serial.line_id == line_id,
            Serial.product_type == "AIO",
            Serial.created_at >= today
        ).scalar()

        mnt = db.query(func.count()).filter(
            Serial.line_id == line_id,
            Serial.product_type == "MNT",
            Serial.created_at >= today
        ).scalar()

        case = db.query(func.count()).filter(
            Serial.line_id == line_id,
            Serial.product_type == "CASE",
            Serial.created_at >= today
        ).scalar()

        nb = db.query(func.count()).filter(
            Serial.line_id == line_id,
            Serial.product_type == "NB",
            Serial.created_at >= today
        ).scalar()

        actual_count = db.query(func.count()).filter(
            Serial.line_id == line_id,
            Serial.created_at >= today
        ).scalar()

        aio_equivalent = (

            aio

            + (mnt * 0.60)

            + (case * 0.80)

            + nb

        )

        difference = aio_equivalent - expected_count

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
    today = datetime.now().replace(
        hour=0,
        minute=0,
        second=0,
        microsecond=0
    )
    db = SessionLocal()

    try:

        count = db.query(func.count()).filter(
            SwitchLog.line_id == line_id,
            SwitchLog.created_at >= today
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
    today = datetime.now().replace(

    hour=0,

    minute=0,

    second=0,

    microsecond=0

    )

    db = SessionLocal()

    try:

        result = []

        for line_id in range(1,7):

            actual_count = db.query(
                func.count()
            ).filter(
                Serial.line_id == line_id,
                Serial.created_at >= today
            ).scalar()

            aio = db.query(func.count()).filter(
                Serial.line_id == line_id,
                Serial.product_type == "AIO",
                Serial.created_at >= today
            ).scalar()

            mnt = db.query(func.count()).filter(
                Serial.line_id == line_id,
                Serial.product_type == "MNT",
                Serial.created_at >= today
            ).scalar()

            case = db.query(func.count()).filter(
                Serial.line_id == line_id,
                Serial.product_type == "CASE",
                Serial.created_at >= today
            ).scalar()

            nb = db.query(func.count()).filter(
                Serial.line_id == line_id,
                Serial.product_type == "NB",
                Serial.created_at >= today
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
                LineStop.line_id == line_id,
                LineStop.created_at >= today
            ).scalar()

            switch_count = db.query(
                func.count()
            ).filter(
                SwitchLog.line_id == line_id,
                SwitchLog.created_at >= today
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

@app.get("/supervisor/{line_id}")
def supervisor_page(

    request: Request,

    line_id: int

):

    return templates.TemplateResponse(
        request=request,
        name="supervisor.html",
        context={
            "line_id": line_id
        }
    )

@app.get("/stop/{line_id}")
def stop_page(
    request: Request,
    line_id: int
):

    return templates.TemplateResponse(
        request=request,
        name="stop.html",
        context={
            "line_id": line_id
        }
    )

@app.get("/api/stop/{line_id}")
def get_stops(line_id: int):

    db = SessionLocal()

    try:

        stops = db.query(
            LineStop
        ).filter(

            LineStop.line_id == line_id

        ).order_by(

            LineStop.id.desc()

        ).limit(10).all()

        result = []

        for stop in stops:

            jalali_date = (
                jdatetime.datetime.fromgregorian(
                    datetime=stop.created_at
                )
            )

            result.append({

                "minutes":
                stop.stop_minutes,

                "time":
                jalali_date.strftime(
                    "%Y/%m/%d %H:%M"
                )

            })

        return result

    finally:

        db.close()

@app.get("/switch/{line_id}")
def switch_page(
    request: Request,
    line_id: int
):

    return templates.TemplateResponse(
        request=request,
        name="switch.html",
        context={
            "line_id": line_id
        }
    )

@app.get("/api/switch/{line_id}")
def get_switches(line_id: int):

    db = SessionLocal()

    try:

        switches = db.query(
            SwitchLog
        ).filter(

            SwitchLog.line_id == line_id

        ).order_by(

            SwitchLog.id.desc()

        ).limit(10).all()

        result = []

        for switch in switches:

            jalali_date = (
                jdatetime.datetime.fromgregorian(
                    datetime=switch.created_at
                )
            )

            result.append({

                "time":
                jalali_date.strftime(
                    "%Y/%m/%d %H:%M"
                )

            })

        return result

    finally:

        db.close()


@app.get("/admin")
def admin_page(request: Request):

    return templates.TemplateResponse(
        request=request,
        name="admin.html",
        context={
            "request": request
        }

    )

@app.get("/api/users")
def get_users():

    db = SessionLocal()

    try:

        users = db.query(User).all()

        return [

            {

                "id":
                user.id,

                "username":
                user.username,

                "role":
                user.role,

                "line_id":
                user.line_id

            }

            for user in users

        ]

    finally:

        db.close()

@app.post("/api/users")
def create_user(
    data: UserCreate
):

    db = SessionLocal()

    try:

        exists = db.query(
            User
        ).filter(

            User.username ==
            data.username

        ).first()

        if exists:

            return {

                "error":
                "Username Exists"

            }

        user = User(

            username=data.username,

            password=data.password,

            role=data.role,

            line_id=data.line_id

        )

        db.add(user)

        db.commit()

        return {

            "message":
            "User Created"

        }

    finally:

        db.close()

@app.delete("/api/users/{user_id}")
def delete_user(user_id: int):

    db = SessionLocal()

    try:

        user = db.query(
            User
        ).filter(

            User.id == user_id

        ).first()

        if not user:

            return {

                "error":
                "User Not Found"

            }

        if user.role == "admin":

            return {

                "error":
                "Cannot Delete Admin"

            }

        db.delete(user)

        db.commit()

        return {

            "message":
            "User Deleted"

        }

    finally:

        db.close()

@app.put("/api/users/{user_id}")
def update_user(
    user_id: int,
    data: UserUpdate
):

    db = SessionLocal()

    try:

        user = db.query(
            User
        ).filter(

            User.id == user_id

        ).first()

        if not user:

            return {

                "error":
                "User Not Found"

            }

        if user.role == "admin":

            return {

                "error":
                "Cannot Modify Admin"

            }

        user.role = data.role

        user.line_id = data.line_id

        db.commit()

        return {

            "message":
            "User Updated"

        }

    finally:

        db.close()


@app.get("/admin/export")
def admin_export(
    request: Request
):

    return templates.TemplateResponse(
        request=request,
        name="admin_export.html",
        context={
            "request": request
        }

    )

@app.get("/admin/users")
def admin_users(
    request: Request
):

    return templates.TemplateResponse(
        request=request,
        name="admin_users.html",
        context={
            "request": request
        }
    )

@app.get("/admin/export")
def export_page(request: Request):

    return templates.TemplateResponse(
        request=request,
        name="admin_export.html",
        context={
            "request": request
        }

    )

@app.get("/api/export")

def export_excel():

    file_path = export_all_production()

    return FileResponse(

        path=file_path,

        filename="Production_Report.xlsx",

        media_type=
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

    )

@app.get("/api/ordercodes")
def get_ordercodes():

    db = SessionLocal()

    try:

        orders = db.query(
            OrderCode
        ).order_by(

            OrderCode.id.desc()

        ).limit(20).all()

        return [

            {

                "order_code":
                item.order_code,

                "product_type":
                item.product_type

            }

            for item in orders

        ]

    finally:

        db.close()


@app.get("/serial-history/{line_id}")
def serial_history(
    request: Request,
    line_id: int
):

    return templates.TemplateResponse(
        request=request,
        name="serial_history.html",
        context={
            "line_id": line_id
        }
    )

@app.get("/api/serial-history/{line_id}")
def serial_history_api(line_id:int, search: str=""):

    db=SessionLocal()

    try:

        query = (

            db.query(Serial)

            .filter(

                Serial.line_id == line_id

            )

        )

        if search:

            query = query.filter(

                or_(

                    Serial.order_number.contains(search),

                    Serial.serial_number.contains(search)

                )

            )

        serials = (

            query

            .order_by(

                Serial.id.desc()

            )

            .all()

        )

        result=[]

        for item in serials:

            result.append({

                "id":item.id,

                "time":item.created_at.strftime("%Y/%m/%d %H:%M"),

                "order":item.order_number,

                "serial":item.serial_number

            })

        return result

    finally:

        db.close()

@app.get("/edit-serial/{serial_id}")
def edit_serial_page(

    request: Request,

    serial_id: int

):

    return templates.TemplateResponse(
        request=request,
        name="edit_serial.html",
        context={
            "request": request,
            "serial_id": serial_id
        }
    )


@app.put("/api/serial/{serial_id}")
def update_serial(
    serial_id:int,
    data:SerialUpdate
):

    db=SessionLocal()

    try:

        serial=db.query(Serial).filter(
            Serial.id==serial_id
        ).first()

        if not serial:

            return {"error":"Not Found"}

        serial.order_number=data.order_number

        serial.serial_number=data.serial_number

        db.commit()

        return {"message":"Updated"}

    finally:

        db.close()

@app.get("/api/serial/{serial_id}")
def get_serial(serial_id:int):

    db = SessionLocal()

    try:

        serial = (

            db.query(Serial)

            .filter(
                Serial.id == serial_id
            )

            .first()

        )

        if not serial:

            return {

                "error":"Serial Not Found"

            }

        return {

            "id":serial.id,

            "order_number":serial.order_number,

            "serial_number":serial.serial_number,

            "line_id":serial.line_id,

            "time":serial.created_at.strftime("%Y/%m/%d %H:%M")

        }

    finally:

        db.close()

@app.get("/api/export/today")
def export_today():

    file_path = export_production()
    return FileResponse(
        path=file_path,

        filename="Production_today_report.xlsx",

        media_type=
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
     )

@app.get("/api/serials/{line_id}")
def serial_history(line_id: int):

    db = SessionLocal()

    try:

        serials = (
            db.query(Serial)
            .filter(Serial.line_id == line_id)
            .order_by(Serial.id.desc())
            .limit(20)
            .all()
        )

        result = []

        for item in serials:

            result.append({

                "time": item.created_at.strftime("%H:%M:%S"),

                "order": item.order_number,

                "serial": item.serial_number

            })

        return result

    finally:

        db.close()