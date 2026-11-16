
import calendar
from datetime import date, timedelta
import time
import traceback
from typing import Literal
from typing import Any
from sqlalchemy import select as sqlalchemy_select, func, case, cast, Float
import re
import tiktoken
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlmodel import Session, select as sqlmodel_select

from app.auth import get_current_user
from app.database import SessionDBKafe, SessionDBKafeLogin, get_session_kafe

from app.model.kafe.AIKnowledge import AIKnowledge
from app.model.kafe.bboreder import Bborder
from app.model.kafe.belanja import Belanja
from app.model.kafe.orderstock import Orderstock
from app.model.kafe.jnsstock import Jnsstock
from app.model.kafe.dailybill import dailybill
from app.model.kafe.member import Member
from app.model.kafe.Pricedetail import Pricedetail
from app.model.kafe.Price import Price

from app.services.OpenAiService import ask_openai
import json
import os
from datetime import date, datetime

from app.model.kafe.ai_conversation import AIConversation
from app.model.kafe.ai_message import AIMessage
from app.model.kafe.ai_feedback import AIFeedback

# SQLAlchemy select wrapper:
# Pylance sometimes cannot infer SQLModel column expression types in aggregate queries.
# Runtime still uses the normal SQLAlchemy db_select() implementation.
def db_select(*entities: Any) -> Any:
    select_function: Any = sqlalchemy_select
    return select_function(*entities)


router = APIRouter()


# ==========================================================
# REQUEST
# ==========================================================

class AIKnowledgeCreateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    content: str = Field(min_length=1)
    category: str | None = Field(default=None, max_length=100)


class AIKnowledgeUpdateRequest(BaseModel):
    title: str | None = Field(default=None, max_length=255)
    content: str | None = None
    category: str | None = Field(default=None, max_length=100)
    status: Literal["active", "archived"] | None = None
class AIFeedbackRequest(BaseModel):
    message_id: int
    rating: int = Field(ge=1, le=5)
    correction: str | None = Field(default=None, max_length=10000)
    comment: str | None = Field(default=None, max_length=3000)


class AIReviewRequest(BaseModel):
    status: Literal["approved", "rejected"]
class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=4000)



class AIChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    conversation_id: int | None = None
    history: list[ChatMessage] = Field(default_factory=list, max_length=12)


# ==========================================================
# HELPER
# ==========================================================

def safe_float(value):
    try:
        if value is None:
            return 0.0

        return float(str(value).replace(",", "."))
    except (ValueError, TypeError):
        return 0.0
def _is_ai_admin(user: Member) -> bool:
    return (
        (user.Divisi or "").strip().lower() == "admin"
        or (user.Status or "").strip().lower() == "spv"
    )

def date_text(value):
    if isinstance(value, date):
        return value.isoformat()

    return str(value) if value is not None else None





def get_period(message: str):
    today = date.today()
    text = message.lower().strip()

    # Semua riwayat
    if any(x in text for x in [
        "semua data",
        "seluruh data",
        "sepanjang waktu",
        "semua riwayat",
        "dari awal"
    ]):
        return None, None

    # Periode khusus
    if "hari ini" in text:
        return today, today

    if "kemarin" in text:
        yesterday = today - timedelta(days=1)
        return yesterday, yesterday

    if "bulan ini" in text:
        return today.replace(day=1), today

    if "bulan lalu" in text:
        first_this_month = today.replace(day=1)
        last_month = first_this_month - timedelta(days=1)
        return last_month.replace(day=1), last_month

    if "tahun ini" in text:
        return date(today.year, 1, 1), today

    if "tahun lalu" in text:
        return (
            date(today.year - 1, 1, 1),
            date(today.year - 1, 12, 31)
        )

    if "minggu ini" in text:
        start = today - timedelta(days=today.weekday())
        return start, today

    if "minggu lalu" in text:
        end = today - timedelta(days=today.weekday() + 1)
        return end - timedelta(days=6), end

    # Tahun tertentu, misalnya 2025
    year_match = re.search(r"\b(20\d{2})\b", text)

    if year_match:
        year = int(year_match.group(1))
        return date(year, 1, 1), date(year, 12, 31)

    # Periode beberapa tahun/bulan/hari terakhir
    period_match = re.search(
        r"\b(\d+)\s*(tahun|bulan|minggu|hari)\b",
        text
    )

    if period_match:
        amount = int(period_match.group(1))
        unit = period_match.group(2)

        if unit == "tahun":
            start = today.replace(
                year=today.year - amount,
                day=min(
                    today.day,
                    calendar.monthrange(
                        today.year - amount,
                        today.month
                    )[1]
                )
            )

        elif unit == "bulan":
            total_month = today.year * 12 + today.month - 1 - amount
            year = total_month // 12
            month = total_month % 12 + 1
            day = min(
                today.day,
                calendar.monthrange(year, month)[1]
            )
            start = date(year, month, day)

        elif unit == "minggu":
            start = today - timedelta(weeks=amount)

        else:
            start = today - timedelta(days=amount)

        return start, today

    # Tidak disebutkan periode = seluruh riwayat
    return None, None

def is_admin_user(user: Member):
    division = (user.Divisi or "").strip().lower()
    status = (user.Status or "").strip().lower()

    return division == "admin" or status == "spv"


# ==========================================================
# DATABASE ANALYTICS
# ==========================================================


def build_database_context(
    session,
    session_login,
    user: Member,
    question: str
):
    today = date.today()

    start_date, end_date = get_period(question)

    is_admin = is_admin_user(user)
    division = (user.Divisi or "").strip()

    def number(value):
        return safe_float(value if value is not None else 0)

    def month_label(year, month):
        if year is None or month is None:
            return "Tidak diketahui"
        return f"{int(year):04d}-{int(month):02d}"

    context = {
        "tanggal_analisis": today.isoformat(),

        "periode": {
            "mulai": date_text(start_date),
            "sampai": date_text(end_date)
        },

        "hak_akses": {
            "admin": is_admin,
            "divisi": division,
            "cakupan": (
                "seluruh data"
                if is_admin
                else f"Data divisi {division} dan data pengguna yang diizinkan"
            )
        },

        "metode_pengolahan": (
            "Seluruh transaksi yang sesuai periode dan hak akses "
            "dihitung melalui agregasi database. Angka total bukan "
            "hasil penjumlahan sampel transaksi."
        ),

        "data": {}
    }

    # ======================================================
    # 1. STOK SEKARANG
    # ======================================================

    stock_rows = session.exec(
        sqlmodel_select(Jnsstock)
        .where(Jnsstock.Aktif == True)
        .order_by(Jnsstock.Jenis)
    ).all()

    context["data"]["stok"] = [
        {
            "jenis": row.Jenis,
            "jumlah": number(row.Jmlh),
            "unit": row.Unit,
            "unit_alternatif": row.Unit1
        }
        for row in stock_rows
    ]

    # ======================================================
    # 2. ORDER STOCK
    # ======================================================

    stock_query = db_select(
        func.substring(Orderstock.Tgl, 1, 7),
        Orderstock.Jenis,
        Orderstock.Divisi,
        func.count(),
        func.sum(Orderstock.Jmlh),
        func.sum(Orderstock.JmlhInp),
        func.sum(Orderstock.JmlhPengiriman),
        func.sum(
            case(
                (Orderstock.Checked == 1, 1),
                else_=0
            )
        )
    )

    if not is_admin:
        stock_query = stock_query.where(
            Orderstock.Divisi == division
        )

    if start_date and end_date:
        stock_query = stock_query.where(
            Orderstock.Tgl >= start_date.isoformat(),
            Orderstock.Tgl <= end_date.isoformat()
        )

    stock_query = stock_query.group_by(
        func.substring(Orderstock.Tgl, 1, 7),
        Orderstock.Jenis,
        Orderstock.Divisi
    ).order_by(
        func.substring(Orderstock.Tgl, 1, 7),
        Orderstock.Jenis
    )

    stock_results = session.execute(stock_query).all()

    context["data"]["order_stock"] = [
        {
            "bulan": row[0],
            "jenis": row[1],
            "divisi": row[2],
            "jumlah_transaksi": int(row[3] or 0),
            "total_order": number(row[4]),
            "total_input": number(row[5]),
            "total_pengiriman": number(row[6]),
            "jumlah_checked": int(row[7] or 0)
        }
        for row in stock_results
    ]

    # ======================================================
    # 3. HEADER PEMBELIAN
    # ======================================================

    order_query = db_select(
        func.year(Bborder.Tgl),
        func.month(Bborder.Tgl),
        Bborder.Category,
        Bborder.Checked,
        func.count(),
        func.sum(Bborder.Total),
        func.sum(Bborder.PengambilanUang),
        func.sum(Bborder.PenambahanUang)
    )

    if start_date and end_date:
        order_query = order_query.where(
            Bborder.Tgl >= start_date,
            Bborder.Tgl <= end_date
        )

    if not is_admin:
        order_query = order_query.where(
            Bborder.Inputer == user.ID
        )

    order_query = order_query.group_by(
        func.year(Bborder.Tgl),
        func.month(Bborder.Tgl),
        Bborder.Category,
        Bborder.Checked
    ).order_by(
        func.year(Bborder.Tgl),
        func.month(Bborder.Tgl)
    )

    order_results = session.execute(order_query).all()

    context["data"]["header_pembelian"] = [
        {
            "bulan": month_label(row[0], row[1]),
            "kategori": row[2],
            "checked": row[3],
            "jumlah_order": int(row[4] or 0),
            "total_tercatat": number(row[5]),
            "total_pengambilan_uang": number(row[6]),
            "total_penambahan_uang": number(row[7])
        }
        for row in order_results
    ]

    # ======================================================
    # 4. DETAIL PEMBELIAN
    #    JOIN BBOrder.IDOrder = Belanja.ID
    # ======================================================

    purchase_query = db_select(
        func.year(Bborder.Tgl),
        func.month(Bborder.Tgl),
        Belanja.Jenis,
        Belanja.Divisi,
        func.count(),
        func.sum(Belanja.JmlhOrder),
        func.sum(Belanja.JmlhPenerima),
        func.sum(Belanja.Jmlh),
        func.sum(
            Belanja.Jmlh * Belanja.Price
        ),
        func.avg(Belanja.Price)
    ).select_from(
        Bborder
    ).join(
        Belanja,
        Belanja.ID == Bborder.IDOrder
    )

    if start_date and end_date:
        purchase_query = purchase_query.where(
            Bborder.Tgl >= start_date,
            Bborder.Tgl <= end_date
        )

    if not is_admin:
        purchase_query = purchase_query.where(
            Bborder.Inputer == user.ID,
            Belanja.Divisi == division
        )

    purchase_query = purchase_query.group_by(
        func.year(Bborder.Tgl),
        func.month(Bborder.Tgl),
        Belanja.Jenis,
        Belanja.Divisi
    ).order_by(
        func.year(Bborder.Tgl),
        func.month(Bborder.Tgl),
        Belanja.Jenis
    )

    purchase_results = session.execute(purchase_query).all()

    context["data"]["detail_pembelian"] = [
        {
            "bulan": month_label(row[0], row[1]),
            "jenis": row[2],
            "divisi": row[3],
            "jumlah_baris_transaksi": int(row[4] or 0),
            "total_jumlah_order": number(row[5]),
            "total_jumlah_penerima": number(row[6]),
            "total_jumlah": number(row[7]),
            "total_nilai_pembelian": number(row[8]),
            "rata_rata_harga": number(row[9])
        }
        for row in purchase_results
    ]

    # ======================================================
    # 5. HARGA SEKARANG
    # ======================================================

    price_rows = session.exec(
        sqlmodel_select(Price).order_by(Price.Jenis)
    ).all()

    context["data"]["harga_sekarang"] = [
        {
            "jenis": row.Jenis,
            "harga": number(row.Price)
        }
        for row in price_rows
    ]

    # ======================================================
    # 6. RIWAYAT HARGA
    # ======================================================

    price_history_query = db_select(
        Pricedetail.Jenis,
        func.count(),
        func.min(Pricedetail.Jmlh),
        func.max(Pricedetail.Jmlh),
        func.avg(Pricedetail.Jmlh),
        func.max(Pricedetail.Tgl)
    )

    if start_date and end_date:
        price_history_query = price_history_query.where(
            Pricedetail.Tgl >= start_date,
            Pricedetail.Tgl <= end_date
        )

    price_history_query = price_history_query.group_by(
        Pricedetail.Jenis
    ).order_by(
        Pricedetail.Jenis
    )

    price_history_results = session.execute(
        price_history_query
    ).all()

    context["data"]["riwayat_harga"] = [
        {
            "jenis": row[0],
            "jumlah_perubahan": int(row[1] or 0),
            "harga_terendah": number(row[2]),
            "harga_tertinggi": number(row[3]),
            "rata_rata_harga": number(row[4]),
            "perubahan_terakhir": date_text(row[5])
        }
        for row in price_history_results
    ]

    # ======================================================
    # 7. DAILY BILL DAN PINJAMAN
    # ======================================================

    bill_query = db_select(
        func.year(dailybill.Bulan),
        func.month(dailybill.Bulan),
        dailybill.Ket,
        dailybill.Lunas,
        func.count(),
        func.sum(
            cast(dailybill.Jmlh, Float)
        )
    )

    if start_date and end_date:
        bill_query = bill_query.where(
            dailybill.Bulan >= start_date,
            dailybill.Bulan <= end_date
        )

    if not is_admin:
        bill_query = bill_query.where(
            dailybill.ID == user.ID
        )

    bill_query = bill_query.group_by(
        func.year(dailybill.Bulan),
        func.month(dailybill.Bulan),
        dailybill.Ket,
        dailybill.Lunas
    ).order_by(
        func.year(dailybill.Bulan),
        func.month(dailybill.Bulan)
    )

    bill_results = session_login.execute(bill_query).all()

    context["data"]["daily_bill"] = [
        {
            "bulan": month_label(row[0], row[1]),
            "kategori": row[2],
            "lunas": row[3],
            "jumlah_transaksi": int(row[4] or 0),
            "total_jumlah": number(row[5])
        }
        for row in bill_results
    ]

    # ======================================================
    # 8. RINGKASAN JUMLAH KELOMPOK
    # ======================================================

    jumlah_kelompok = {
        "stok": len(stock_rows),
        "order_stock": len(stock_results),
        "header_pembelian": len(order_results),
        "detail_pembelian": len(purchase_results),
        "harga_sekarang": len(price_rows),
        "riwayat_harga": len(price_history_results),
        "daily_bill": len(bill_results)
    }

    context["catatan"] = {
        "data_penjualan": False,
        "data_laba": False,

        "data_pinjaman": (
            "Kategori pinjaman dan bon dikenali melalui kolom Ket. "
            "Status lunas tersedia. Riwayat cicilan terpisah belum tersedia."
        ),

        "jumlah_kelompok": jumlah_kelompok,

        "keterangan": (
            "Data transaksi dihitung menggunakan agregasi database "
            "berdasarkan seluruh baris yang sesuai periode dan hak akses. "
            "Jumlah kelompok bukan jumlah transaksi mentah."
        ),

        "catatan_perhitungan": (
            "Nilai pembelian detail dihitung dari jumlah dikalikan harga. "
            "Nilai tersebut merupakan nilai detail, bukan otomatis "
            "total kas yang dibayarkan."
        )
    }

    return context


# ==========================================================
# PEMADATAN CONTEXT AGAR INPUT TIDAK MELEBIHI LIMIT TOKEN
# ==========================================================

CONTEXT_TOKEN_BUDGET = int(os.getenv("AI_CONTEXT_TOKEN_BUDGET", "65000"))
MAX_ROWS_PER_SECTION = int(os.getenv("AI_CONTEXT_MAX_ROWS", "250"))


def _token_encoder():
    model = os.getenv("OPENAI_MODEL", "gpt-6.1-sol").strip()
    try:
        return tiktoken.encoding_for_model(model)
    except Exception:
        try:
            return tiktoken.get_encoding("o200k_base")
        except Exception:
            return tiktoken.get_encoding("cl100k_base")


def _count_text_tokens(value: str) -> int:
    try:
        return len(_token_encoder().encode(value))
    except Exception:
        # Fallback konservatif bila tokenizer gagal.
        return max(1, len(value) // 3)


def _merge_monthly_rows(rows: list[dict], section: str) -> list[dict]:
    """Gabungkan kelompok bulanan menjadi total per item selama periode.

    Semua baris sumber sudah merupakan hasil agregasi SQL; penggabungan ini
    mempertahankan total numerik tanpa mengirim satu baris untuk setiap bulan.
    """
    if not rows:
        return rows

    if section == "order_stock":
        keys = ("jenis", "divisi")
        sum_fields = ("jumlah_transaksi", "total_order", "total_input", "total_pengiriman", "jumlah_checked")
    elif section == "header_pembelian":
        keys = ("kategori", "checked")
        sum_fields = ("jumlah_order", "total_tercatat", "total_pengambilan_uang", "total_penambahan_uang")
    elif section == "detail_pembelian":
        keys = ("jenis", "divisi")
        sum_fields = ("jumlah_baris_transaksi", "total_jumlah_order", "total_jumlah_penerima", "total_jumlah", "total_nilai_pembelian")
    elif section == "daily_bill":
        keys = ("kategori", "lunas")
        sum_fields = ("jumlah_transaksi", "total_jumlah")
    else:
        return rows

    merged: dict[tuple, dict] = {}
    weighted_price: dict[tuple, float] = {}
    weighted_count: dict[tuple, float] = {}

    for row in rows:
        key = tuple(row.get(k) for k in keys)
        if key not in merged:
            merged[key] = {k: row.get(k) for k in keys}
            for field in sum_fields:
                merged[key][field] = 0
            if "rata_rata_harga" in row:
                merged[key]["rata_rata_harga"] = 0
                weighted_price[key] = 0.0
                weighted_count[key] = 0.0

        target = merged[key]
        for field in sum_fields:
            target[field] += safe_float(row.get(field))

        if "rata_rata_harga" in row:
            count = safe_float(row.get("jumlah_baris_transaksi"))
            weighted_price[key] += safe_float(row.get("rata_rata_harga")) * count
            weighted_count[key] += count

    result = list(merged.values())
    for row in result:
        key = tuple(row.get(k) for k in keys)
        if key in weighted_price:
            row["rata_rata_harga"] = (
                weighted_price[key] / weighted_count[key]
                if weighted_count[key] else 0
            )
    return result


def compact_database_context(context: dict, question: str) -> dict:
    """Padatkan hasil agregasi, tetap menyertakan indikator data yang dipotong."""
    data = context.get("data", {})
    monthly_requested = any(term in question.lower() for term in (
        "per bulan", "tiap bulan", "bulanan", "tren bulanan", "trend bulanan",
        "perbandingan bulan", "bandingkan bulan", "monthly"
    ))

    # Pertanyaan umum tidak memerlukan satu baris untuk setiap bulan.
    if not monthly_requested:
        for section in ("order_stock", "header_pembelian", "detail_pembelian", "daily_bill"):
            if isinstance(data.get(section), list):
                data[section] = _merge_monthly_rows(data[section], section)

    omitted = {}
    for section, rows in list(data.items()):
        if not isinstance(rows, list):
            continue
        original_count = len(rows)
        # Untuk pertanyaan tren bulanan, tetap batasi jumlah titik agar prompt aman.
        limit = MAX_ROWS_PER_SECTION if not monthly_requested else min(MAX_ROWS_PER_SECTION, 500)
        if original_count > limit:
            data[section] = rows[:limit]
            omitted[section] = {
                "kelompok_tersedia": original_count,
                "kelompok_dikirim": limit,
                "kelompok_tidak_dikirim": original_count - limit
            }

    context.setdefault("catatan", {})["pemadatan_context"] = {
        "mode": "bulanan" if monthly_requested else "total_per_item_selama_periode",
        "keterangan": (
            "Data dikelompokkan per bulan untuk pertanyaan tren; hasil yang melebihi batas ditandai sebagai tidak lengkap."
            if monthly_requested else
            "Untuk menghemat token, data bulanan digabung menjadi total per jenis/kategori selama periode yang diminta."
        ),
        "kelompok_dibatasi": omitted,
        "peringatan": (
            "Jangan menyimpulkan peringkat atau total dari daftar yang dipotong sebagai keseluruhan data."
            if omitted else "Tidak ada kelompok yang dipotong."
        )
    }
    return context


def fit_context_to_token_budget(context: dict, question: str) -> tuple[dict, int]:
    """Batas keras tambahan agar prompt tidak mendekati limit provider."""
    data = context.get("data", {})
    budget = max(10000, CONTEXT_TOKEN_BUDGET)

    def serialize_and_count() -> tuple[str, int]:
        raw = json.dumps(context, ensure_ascii=False, default=str, separators=(",", ":"))
        return raw, _count_text_tokens(raw)

    raw, tokens = serialize_and_count()
    if tokens <= budget:
        return context, tokens

    # Kurangi jumlah detail bertahap. Total data DB sudah dihitung oleh query,
    # tetapi detail kelompok yang tidak terkirim diberi peringatan eksplisit.
    for limit in (150, 100, 60, 30, 15):
        for section, rows in list(data.items()):
            if isinstance(rows, list) and len(rows) > limit:
                data[section] = rows[:limit]
        raw, tokens = serialize_and_count()
        if tokens <= budget:
            context.setdefault("catatan", {}).setdefault("pemadatan_context", {})["batas_token"] = {
                "target_token": budget,
                "token_context": tokens,
                "keterangan": "Sebagian detail kelompok tidak dikirim agar permintaan tidak melewati batas token."
            }
            raw, tokens = serialize_and_count()
            return context, tokens

    # Jika data stok/harga/knowledge masih sangat besar, potong daftar terbesar.
    while tokens > budget:
        candidates = [(len(v), k) for k, v in data.items() if isinstance(v, list) and len(v) > 1]
        if not candidates:
            break
        _, section = max(candidates)
        data[section] = data[section][:max(1, len(data[section]) // 2)]
        raw, tokens = serialize_and_count()

    context.setdefault("catatan", {}).setdefault("pemadatan_context", {})["batas_token"] = {
        "target_token": budget,
        "token_context": tokens,
        "keterangan": "Context dipadatkan otomatis. Periksa indikator kelompok yang tidak dikirim sebelum membuat kesimpulan rinci."
    }
    raw, tokens = serialize_and_count()
    return context, tokens


@router.post("/chat")
def chat_with_ai(
    request: AIChatRequest,
    session: SessionDBKafe,
    session_login: SessionDBKafeLogin,
    current_user: Member = Depends(get_current_user),
):
    start = time.time()

    try:
        print("[AI] Memulai chat")

        # --------------------------------------------------
        # 1. VALIDASI USER
        # --------------------------------------------------

        if not current_user or not current_user.Active:
            raise HTTPException(
                status_code=403,
                detail="Akun tidak aktif"
            )

        # --------------------------------------------------
        # 2. AMBIL ATAU BUAT CONVERSATION
        # --------------------------------------------------

        conversation = None

        if request.conversation_id:
            conversation = session.exec(
                sqlmodel_select(AIConversation).where(
                    AIConversation.ID == request.conversation_id,
                    AIConversation.UserID == current_user.ID
                )
            ).first()

            if not conversation:
                raise HTTPException(
                    status_code=404,
                    detail="Percakapan tidak ditemukan"
                )

        else:
            conversation = AIConversation(
                UserID=current_user.ID,
                Title=request.message[:100],
            )

            session.add(conversation)
            session.commit()
            session.refresh(conversation)

        print(
            "[AI] Conversation siap:",
            f"{time.time() - start:.2f}s"
        )

        # --------------------------------------------------
        # 3. DATABASE CONTEXT
        # --------------------------------------------------

        print("[AI] Membuat database context")

        context = build_database_context(
            session,
            session_login,
            current_user,
            request.message
        )

        context = compact_database_context(context, request.message)
        context, context_tokens = fit_context_to_token_budget(context, request.message)
        context_json = json.dumps(
            context,
            ensure_ascii=False,
            default=str,
            separators=(",", ":")
        )

        print("[AI CONTEXT] Ukuran JSON:", len(context_json), "karakter")
        print("[AI CONTEXT] Token context:", f"{context_tokens:,}")

        print(
            "[AI CONTEXT] Jumlah baris:",
            context.get("catatan", {}).get("jumlah_kelompok", {})
        )

        print(
            "[AI] Database context selesai:",
            f"{time.time() - start:.2f}s"
        )

        # --------------------------------------------------
        # 4. RIWAYAT PERCAKAPAN
        # --------------------------------------------------

        history = session.exec(
            sqlmodel_select(AIMessage)
            .where(
                AIMessage.ConversationID == conversation.ID,
                AIMessage.UserID == current_user.ID,
                AIMessage.Role.in_(["user", "assistant"])
            )
            .order_by(AIMessage.CreatedAt.desc())
            .limit(8)
        ).all()
        history = list(reversed(history))

        # --------------------------------------------------
        # 5. SYSTEM PROMPT
        # --------------------------------------------------

        system_prompt = f"""
Kamu adalah CoffeeDay Intelligence,
AI analis data operasional dan keuangan CoffeeDay.

TUGAS:
- Analisis data operasional dan keuangan CoffeeDay.
- Jawab berdasarkan data database yang diberikan.
- Lakukan perhitungan sendiri jika diperlukan.
- Jangan mengarang angka atau informasi.
- Jika data tidak tersedia, katakan dengan jujur.
- Gunakan bahasa Indonesia.
- Berikan jawaban ringkas, jelas, dan terstruktur.
- Gunakan tabel jika membantu memahami hasil.
- Berikan kesimpulan berdasarkan hasil analisis.

ATURAN DATA:
- Gunakan seluruh ringkasan agregat yang tersedia dalam database context.
- Jika catatan pemadatan menyatakan ada kelompok yang tidak dikirim, jangan mengklaim daftar detail sebagai keseluruhan data.
- Untuk total keseluruhan, utamakan nilai agregat yang tersedia; jika tidak tersedia, jelaskan keterbatasannya.
- Jangan membatasi periode analisis secara sepihak.
- Jika pengguna meminta satu tahun, gunakan seluruh data
  yang tersedia dalam rentang satu tahun tersebut.
- Jangan menganggap data yang tidak tersedia sebagai nol.
- Jangan menggandakan transaksi ketika menggabungkan tabel.

ATURAN JAWABAN:
- Jangan menampilkan SQL secara otomatis.
- Jangan menampilkan rumus secara otomatis.
- Jangan menampilkan proses perhitungan secara otomatis.
- Tampilkan SQL, rumus, dan proses perhitungan hanya jika
  pengguna secara eksplisit memintanya.
- Perhitungan internal tetap boleh dilakukan.
- Utamakan hasil, angka, perbandingan, dan kesimpulan.

RELASI DATABASE:
- BBOrder.IDOrder merupakan ID utama pesanan.
- OrderStok.IDOrder terhubung ke BBOrder.IDOrder.
- Belanja.ID terhubung ke BBOrder.IDOrder.
- Hindari penggandaan transaksi saat melakukan perhitungan.

BATAS AKSES:
{context.get("hak_akses", {}).get(
    "cakupan",
    "Sesuai hak akses pengguna"
)}

DATA DATABASE COFFEEDAY:
{context_json}
"""

        messages = [
            {
                "role": "system",
                "content": system_prompt
            }
        ]

        # --------------------------------------------------
        # 6. TAMBAHKAN HISTORY
        # --------------------------------------------------

        for item in history[-8:]:
            if item.Role in ("user", "assistant"):
                messages.append({
                    "role": item.Role,
                    "content": (item.Content or "")[:2500]
                })

        # --------------------------------------------------
        # 7. PERTANYAAN TERBARU
        # --------------------------------------------------

        messages.append({
            "role": "user",
            "content": request.message
        })

        # --------------------------------------------------
        # 8. HITUNG ESTIMASI TOKEN + BATAS PENGAMAN
        # --------------------------------------------------

        total_text = "\n".join(
            str(message.get("content", "")) for message in messages
        )
        estimated_tokens = _count_text_tokens(total_text)

        # Sisakan ruang untuk format pesan dan variasi tokenizer provider.
        MAX_INPUT_TOKENS = int(os.getenv("AI_MAX_INPUT_TOKENS", "80000"))
        print("[AI CONTEXT] Estimasi seluruh token:", f"{estimated_tokens:,}")

        if estimated_tokens > MAX_INPUT_TOKENS:
            # Riwayat dihapus lebih dahulu; database context tidak diubah.
            messages = [messages[0], messages[-1]]
            total_text = "\n".join(str(m.get("content", "")) for m in messages)
            estimated_tokens = _count_text_tokens(total_text)

        if estimated_tokens > MAX_INPUT_TOKENS:
            raise HTTPException(
                status_code=413,
                detail=(
                    f"Konteks analisis masih terlalu besar ({estimated_tokens:,} token). "
                    "Persempit periode atau gunakan pertanyaan yang lebih spesifik."
                )
            )

        # --------------------------------------------------
        # 9. KIRIM KE OPENAI
        # --------------------------------------------------

        print("[AI] Mengirim request ke OpenAI")

        reply, usage = ask_openai(messages)

        print("[AI] OpenAI berhasil")
        print("[AI] Usage:", usage)
        print("[AI] Panjang jawaban:", len(reply or ""))

        print(
            "[AI] OpenAI selesai:",
            f"{time.time() - start:.2f}s"
        )

        # --------------------------------------------------
        # 10. SIMPAN PESAN USER
        # --------------------------------------------------

        user_message = AIMessage(
            ConversationID=conversation.ID,
            UserID=current_user.ID,
            Role="user",
            Content=request.message
        )

        session.add(user_message)
        session.commit()
        session.refresh(user_message)

        # --------------------------------------------------
        # 11. SIMPAN JAWABAN AI
        # --------------------------------------------------

        assistant_message = AIMessage(
            ConversationID=conversation.ID,
            UserID=current_user.ID,
            Role="assistant",
            Content=reply,
            Provider="openai",
            Model=os.getenv(
                "OPENAI_MODEL",
                "gpt-6.1-sol"
            ),
            PromptTokens=int(
                (usage or {}).get("prompt_tokens") or 0
            ),
            CompletionTokens=int(
                (usage or {}).get("completion_tokens") or 0
            ),
        )

        session.add(assistant_message)

        # --------------------------------------------------
        # 12. UPDATE CONVERSATION
        # --------------------------------------------------

        conversation.UpdatedAt = datetime.now()

        session.add(conversation)
        session.commit()
        session.refresh(assistant_message)

        print(
            "[AI] Chat selesai total:",
            f"{time.time() - start:.2f}s"
        )

        # --------------------------------------------------
        # 13. RESPONSE
        # --------------------------------------------------

        return {
            "conversation_id": conversation.ID,
            "user_message_id": user_message.ID,
            "assistant_message_id": assistant_message.ID,
            "reply": reply,
            "provider": "openai",
            "model": os.getenv(
                "OPENAI_MODEL",
                "gpt-6.1-sol"
            ),
            "usage": usage,
            "estimated_tokens": estimated_tokens
        }

    except HTTPException:
        session.rollback()
        raise

    except Exception as e:
        session.rollback()

        print("[AI ERROR]", repr(e))

        raise HTTPException(
            status_code=500,
            detail=f"Gagal memproses AI: {str(e)}"
        )

@router.get("/conversations/{conversation_id}/messages")
def get_conversation_messages(
    conversation_id: int,
    session: SessionDBKafe,
    current_user: Member = Depends(get_current_user),
):
    conversation = session.exec(
        sqlmodel_select(AIConversation).where(
            AIConversation.ID == conversation_id,
            AIConversation.UserID == current_user.ID,
        )
    ).first()

    if not conversation:
        raise HTTPException(
            status_code=404,
            detail="Percakapan tidak ditemukan."
        )

    messages = session.exec(
        sqlmodel_select(AIMessage)
        .where(
            AIMessage.ConversationID == conversation_id,
            AIMessage.UserID == current_user.ID,
        )
        .order_by(AIMessage.CreatedAt.asc())
    ).all()

    return {
        "conversation_id": conversation_id,
        "messages": messages,
    }
@router.post("/feedback")
def submit_ai_feedback(
    request: AIFeedbackRequest,
    session: SessionDBKafe,
    current_user: Member = Depends(get_current_user)
):
    message = session.exec(
        sqlmodel_select(AIMessage).where(
            AIMessage.ID == request.message_id,
            AIMessage.UserID == current_user.ID,
            AIMessage.Role == "assistant"
        )
    ).first()

    if not message:
        raise HTTPException(
            status_code=404,
            detail="Jawaban AI tidak ditemukan."
        )

    existing = session.exec(
        sqlmodel_select(AIFeedback).where(
            AIFeedback.MessageID == request.message_id,
            AIFeedback.UserID == current_user.ID
        )
    ).first()

    if existing:
        existing.Rating = request.rating
        existing.Correction = request.correction
        existing.Comment = request.comment
        existing.Status = "pending"
        existing.ReviewedBy = None
        session.add(existing)
    else:
        feedback = AIFeedback(
            MessageID=request.message_id,
            UserID=current_user.ID,
            Rating=request.rating,
            Correction=request.correction,
            Comment=request.comment,
            Status="pending"
        )
        session.add(feedback)

    session.commit()

    return {
        "message": "Feedback berhasil disimpan.",
        "status": "pending"
    }
@router.patch("/feedback/{feedback_id}/review")
def review_ai_feedback(
    feedback_id: int,
    request: AIReviewRequest,
    session: SessionDBKafe,
    current_user: Member = Depends(get_current_user)
):
    is_admin = (
        (current_user.Divisi or "").strip().lower() == "admin"
        or (current_user.Status or "").strip().lower() == "spv"
    )

    if not is_admin:
        raise HTTPException(
            status_code=403,
            detail="Hanya admin yang dapat meninjau feedback."
        )

    feedback = session.get(AIFeedback, feedback_id)

    if not feedback:
        raise HTTPException(
            status_code=404,
            detail="Feedback tidak ditemukan."
        )

    if feedback.Status != "pending":
        raise HTTPException(
            status_code=400,
            detail="Feedback sudah pernah ditinjau."
        )

    feedback.Status = request.status
    feedback.ReviewedBy = current_user.ID

    session.add(feedback)
    session.commit()

    return {
        "message": "Feedback berhasil ditinjau.",
        "status": feedback.Status
    }
@router.get("/knowledge")
def get_ai_knowledge(
    session: SessionDBKafe,
    current_user: Member = Depends(get_current_user)
):
    if not _is_ai_admin(current_user):
        raise HTTPException(status_code=403, detail="Akses ditolak")

    rows = session.exec(
        sqlmodel_select(AIKnowledge)
        .order_by(AIKnowledge.CreatedAt.desc())
    ).all()

    return {
        "total": len(rows),
        "data": rows
    }
@router.patch("/knowledge/{knowledge_id}")
def update_ai_knowledge(
    knowledge_id: int,
    request: AIKnowledgeUpdateRequest,
    session: SessionDBKafe,
    current_user: Member = Depends(get_current_user)
):
    if not _is_ai_admin(current_user):
        raise HTTPException(status_code=403, detail="Akses ditolak")

    knowledge = session.get(AIKnowledge, knowledge_id)

    if not knowledge:
        raise HTTPException(status_code=404, detail="Knowledge tidak ditemukan")

    if request.title is not None:
        title = request.title.strip()
        if not title:
            raise HTTPException(status_code=422, detail="Judul tidak boleh kosong")
        knowledge.Title = title

    if request.content is not None:
        content = request.content.strip()
        if not content:
            raise HTTPException(status_code=422, detail="Isi tidak boleh kosong")
        knowledge.Content = content

    if request.category is not None:
        knowledge.Category = request.category.strip() or None

    if request.status is not None:
        knowledge.Status = request.status

    knowledge.UpdatedAt = datetime.now()

    session.add(knowledge)
    session.commit()
    session.refresh(knowledge)

    return {
        "message": "Knowledge berhasil diperbarui",
        "data": knowledge
    }
@router.delete("/knowledge/{knowledge_id}")
def delete_ai_knowledge(
    knowledge_id: int,
    session: SessionDBKafe,
    current_user: Member = Depends(get_current_user)
):
    if not _is_ai_admin(current_user):
        raise HTTPException(status_code=403, detail="Akses ditolak")

    knowledge = session.get(AIKnowledge, knowledge_id)

    if not knowledge:
        raise HTTPException(status_code=404, detail="Knowledge tidak ditemukan")

    session.delete(knowledge)
    session.commit()

    return {
        "message": "Knowledge berhasil dihapus"
    } 