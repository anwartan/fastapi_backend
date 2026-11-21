
from fastapi import (
    APIRouter,
    Depends,
    WebSocket,
    WebSocketDisconnect,
)
from sqlmodel import select

from app.auth import get_current_user
from app.database import SessionDBKafe, SessionDBKafeLogin
from app.model.kafe.member import Member
from app.request.notifikasiRequest import NotifikasiRequuest

from app.model.kafe.bboreder import Bborder
from app.model.kafe.belanja import Belanja
from app.model.kafe.orderstock import Orderstock

from app.services.notification_ws import (
    connect,
    disconnect,
)

router = APIRouter()


# ============================================================
# UPDATE TOKEN NOTIFIKASI
# ============================================================

@router.post("/")
def notification(
    session: SessionDBKafeLogin,
    req: NotifikasiRequuest,
    current_user: Member = Depends(get_current_user),
):
    current_user.TokenNotifikasi = req.token_notifikasi

    session.add(current_user)
    session.commit()
    session.refresh(current_user)

    return {"message": "Berhasil update"}


# ============================================================
# WEBSOCKET REALTIME
# ============================================================

@router.websocket("/ws")
async def notification_ws(websocket: WebSocket):
    await connect(websocket)

    try:
        while True:
            await websocket.receive_text()

    except WebSocketDisconnect:
        await disconnect(websocket)

    except Exception:
        await disconnect(websocket)


# ============================================================
# HELPER
# ============================================================

def _is_zero_or_none(value):
    try:
        return value is None or float(value) == 0
    except (TypeError, ValueError):
        return True


def _date_to_string(value):
    if value is None:
        return None

    if hasattr(value, "isoformat"):
        return value.isoformat()

    return str(value)


# ============================================================
# NOTIFIKASI PENERIMAAN
# ============================================================

@router.get("/penerimaan")
def get_notifikasi_penerimaan(
    session: SessionDBKafe,
    current_user: Member = Depends(get_current_user),
):
    divisi_user = str(current_user.Divisi or "").strip()

    is_admin = (
        divisi_user.lower() == "admin"
        or str(current_user.Status or "").strip().lower() == "spv"
    )

    grouped = {}

    # ========================================================
    # ORDER BELANJA
    # ========================================================

    belanja_query = (
        select(Belanja, Bborder)
        .join(
            Bborder,
            Belanja.ID == Bborder.IDOrder,
        )
    )

    if not is_admin:
        belanja_query = belanja_query.where(
            Belanja.Divisi == divisi_user
        )

    belanja_rows = session.exec(belanja_query).all()

    for item, header in belanja_rows:

        order_id = header.IDOrder
        key = ("order_belanja", order_id)

        if key not in grouped:
            grouped[key] = {
                "type": "order_belanja",
                "IDOrder": order_id,
                "Tgl": _date_to_string(header.Tgl),
                "divisi": item.Divisi,
                "Ket": header.Ket,
                "PendingItems": 0,
                "TotalItems": 0,
                "HasReception": False,
            }

        grouped[key]["TotalItems"] += 1

        sudah_diterima = (
            not _is_zero_or_none(item.JmlhPenerima)
            and not _is_zero_or_none(item.ID_Penerima)
        )

        if sudah_diterima:
            grouped[key]["HasReception"] = True
        else:
            grouped[key]["PendingItems"] += 1

    # ========================================================
    # ORDER STOCK
    # ========================================================

    stock_query = (
        select(Orderstock, Bborder)
        .join(
            Bborder,
            Orderstock.IDOrder == Bborder.IDOrder,
        )
    )

    if not is_admin:
        stock_query = stock_query.where(
            Orderstock.Divisi == divisi_user
        )

    stock_rows = session.exec(stock_query).all()

    for item, header in stock_rows:

        order_id = header.IDOrder
        key = ("order_stock", order_id)

        if key not in grouped:
            grouped[key] = {
                "type": "order_stock",
                "IDOrder": order_id,
                "Tgl": _date_to_string(header.Tgl),
                "divisi": item.Divisi,
                "Ket": header.Ket,
                "PendingItems": 0,
                "TotalItems": 0,
                "HasReception": False,
            }

        grouped[key]["TotalItems"] += 1

        sudah_diterima = (
            not _is_zero_or_none(item.JmlhInp)
            and not _is_zero_or_none(item.ID_Penerimaan)
        )

        if sudah_diterima:
            grouped[key]["HasReception"] = True
        else:
            grouped[key]["PendingItems"] += 1

    # ========================================================
    # TAMPILKAN ORDER YANG BELUM ADA PENERIMAAN SAMA SEKALI
    # ========================================================

    result = [
        {
            key: value
            for key, value in order.items()
            if key != "HasReception"
        }
        for order in grouped.values()
        if not order["HasReception"]
    ]

    result.sort(
        key=lambda x: (
            x["Tgl"] or "",
            x["IDOrder"] or 0,
        ),
        reverse=True,
    )

    return {
        "data": result,
        "total": len(result),
    }
