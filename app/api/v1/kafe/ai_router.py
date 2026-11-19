
import calendar
from datetime import date, timedelta
import time
import traceback
from typing import Literal
from typing import Any
from sqlalchemy import select as sqlalchemy_select, func, case, cast, Float
import re
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
    """Periode analisis versi lama: maksimal 360 hari (sekitar 12 bulan)."""
    today = date.today()
    text = message.lower().strip()
    max_days = 180

    if "hari ini" in text:
        return today, today
    if "kemarin" in text:
        yesterday = today - timedelta(days=1)
        return yesterday, yesterday
    if "bulan ini" in text:
        return max(today.replace(day=1), today - timedelta(days=max_days)), today
    if "bulan lalu" in text:
        first_this_month = today.replace(day=1)
        last_month = first_this_month - timedelta(days=1)
        return max(last_month.replace(day=1), today - timedelta(days=max_days)), last_month
    if "minggu ini" in text:
        start = today - timedelta(days=today.weekday())
        return max(start, today - timedelta(days=max_days)), today
    if "minggu lalu" in text:
        end = today - timedelta(days=today.weekday() + 1)
        start = end - timedelta(days=6)
        return max(start, today - timedelta(days=max_days)), end

    # Semua permintaan periode dibatasi maksimal 180 hari.
    period_match = re.search(r"\b(\d+)\s*(tahun|thn|th|bulan|minggu|hari)\b", text)
    if period_match:
        amount = int(period_match.group(1))
        unit = period_match.group(2)
        if unit in ("tahun", "thn", "th"):
            requested_days = amount * 365
        elif unit == "bulan":
            requested_days = amount * 30
        elif unit == "minggu":
            requested_days = amount * 7
        else:
            requested_days = amount
        return today - timedelta(days=min(requested_days, max_days)), today

    # Jika user tidak menyebut periode, ambil 180 hari terakhir.
    return today - timedelta(days=max_days), today


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

        context_json = json.dumps(
            context,
            ensure_ascii=False,
            default=str
        )

        print(
            "[AI CONTEXT] Ukuran JSON:",
            len(context_json),
            "karakter"
        )

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
                AIMessage.ConversationID == conversation.ID
            )
            .order_by(AIMessage.CreatedAt)
        ).all()

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
- Gunakan seluruh data yang tersedia dalam database context.
- Jangan membatasi periode analisis secara sepihak.
- Jika pengguna meminta satu tahun, gunakan seluruh data
  yang tersedia dalam rentang satu tahun tersebut.
- Jangan menganggap data yang tidak tersedia sebagai nol.
- Jangan menggandakan transaksi ketika menggabungkan tabel.

ATURAN PERHITUNGAN PEMBELIAN:

- BBOrder.Total merupakan sumber utama nilai pembelian.
- Belanja.Jmlh * Belanja.Price digunakan untuk memverifikasi
  nilai detail pembelian.
- Cocokkan BBOrder.IDOrder dengan Belanja.ID.
- Bandingkan total detail dengan BBOrder.Total untuk setiap IDOrder.
- Jika cocok, gunakan satu nilai transaksi tersebut.
- Jika tidak cocok, gunakan BBOrder.Total.
- Jika detail tidak tersedia, gunakan BBOrder.Total.
- Dilarang menjumlahkan BBOrder.Total dan total detail pembelian.
- Setiap IDOrder hanya boleh dihitung satu kali.
- Jangan menganggap total detail sebagai pengeluaran tambahan.
- Pastikan nol nya benar misalnya jika 100 ribu 100.000.00 bukan 100.000.0000

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

        for item in history[-12:]:
            if item.Role in ("user", "assistant"):
                messages.append({
                    "role": item.Role,
                    "content": item.Content
                })

        # --------------------------------------------------
        # 7. PERTANYAAN TERBARU
        # --------------------------------------------------

        messages.append({
            "role": "user",
            "content": request.message
        })

        # --------------------------------------------------
        # 8. HITUNG ESTIMASI TOKEN
        # --------------------------------------------------

        try:
            total_text = "\n".join(message["content"] for message in messages)
            estimated_tokens = len(total_text) // 4
            print("[AI CONTEXT] Estimasi token kasar:", estimated_tokens)
        except Exception as token_error:
            print("[AI TOKEN ERROR]", repr(token_error))
            estimated_tokens = None

        # --------------------------------------------------
        # 9. KIRIM KE OPENAI
        # --------------------------------------------------

        print("[AI] Mengirim request ke OpenAI")
        session.commit()
        session_login.commit()

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
        try:
            session.rollback()
        except Exception as rollback_error:
            print("[AI] Rollback Kafe error:", repr(rollback_error))

        try:
            session_login.rollback()
        except Exception as rollback_error:
            print("[AI] Rollback Login error:", repr(rollback_error))

        raise

    except Exception as e:
        try:
            session.rollback()
        except Exception as rollback_error:
            print("[AI] Rollback Kafe error:", repr(rollback_error))

        try:
            session_login.rollback()
        except Exception as rollback_error:
            print("[AI] Rollback Login error:", repr(rollback_error))

        print("[AI ERROR]", repr(e))
        traceback.print_exc()

        raise HTTPException(
            status_code=500,
            detail=f"Gagal memproses AI: {str(e)}"
    )
@router.get("/conversations")
def get_ai_conversations(
    session: SessionDBKafe,
    current_user: Member = Depends(get_current_user),
):
    conversations = session.exec(
        sqlmodel_select(AIConversation)
        .where(
            AIConversation.UserID == current_user.ID
        )
        .order_by(
            AIConversation.UpdatedAt.desc()
        )
    ).all()

    return {
        "total": len(conversations),
        "conversations": conversations,
    }

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