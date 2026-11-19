
from fastapi import APIRouter, Depends
from sqlmodel import select

from app.auth import get_current_user
from app.database import SessionDBKafe, SessionDBKafeLogin
from app.model.kafe.member import Member
from app.request.notifikasiRequest import NotifikasiRequuest

from app.model.kafe.bboreder import Bborder
from app.model.kafe.belanja import Belanja
from app.model.kafe.orderstock import Orderstock


router = APIRouter()


# ============================================================
# UPDATE TOKEN NOTIFIKASI — ENDPOINT LAMA
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
# HELPER
# ============================================================

def _is_zero_or_none(value):
    """
    Nilai None atau 0 dianggap belum diterima.
    """
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
# NOTIFIKASI PENERIMAAN BELANJA DAN ORDER STOCK
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

    # --------------------------------------------------------
    # 1. AMBIL ORDER BELANJA
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # 2. AMBIL ORDER STOCK
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # 3. KELOMPOKKAN ORDER BELANJA
    # --------------------------------------------------------

    grouped = {}

    for item, header in belanja_rows:
        order_id = header.IDOrder
        key = ("order_belanja", order_id)

        if key not in grouped:
            grouped[key] = {
                "type": "order_belanja",
                "IDOrder": order_id,
                "Tgl": _date_to_string(header.Tgl),
                "Ket": header.Ket,
                "PendingItems": 0,
                "TotalItems": 0,
            }

        grouped[key]["TotalItems"] += 1

        belum_diterima = (
            _is_zero_or_none(item.JmlhPenerima)
            or _is_zero_or_none(item.ID_Penerima)
        )

        if belum_diterima:
            grouped[key]["PendingItems"] += 1

    # --------------------------------------------------------
    # 4. KELOMPOKKAN ORDER STOCK
    # --------------------------------------------------------

    for item, header in stock_rows:
        order_id = header.IDOrder
        key = ("order_stock", order_id)
        if key not in grouped:
            grouped[key] = {
                "type": "order_stock",
                "IDOrder": order_id,
                "Tgl": _date_to_string(header.Tgl),
                "Ket": header.Ket,
                "PendingItems": 0,
                "TotalItems": 0,
            }

        grouped[key]["TotalItems"] += 1

        belum_diterima = (
            _is_zero_or_none(item.JmlhInp)
            or _is_zero_or_none(item.ID_Penerimaan)
        )

        if belum_diterima:
            grouped[key]["PendingItems"] += 1

    # --------------------------------------------------------
    # 5. TAMPILKAN HANYA ORDER YANG MASIH PUNYA PENERIMAAN
    #    BELUM SELESAI
    # --------------------------------------------------------

    result = [
        order
        for order in grouped.values()
        if order["PendingItems"] > 0
    ]

    # Terbaru ditampilkan lebih dahulu.
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
