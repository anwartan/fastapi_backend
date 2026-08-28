from fastapi import APIRouter, Depends
from sqlmodel import select

from app.auth import get_current_user
from app.database import SessionDBKafeLogin
from app.model.kafe.dailybill import dailybill
from app.model.kafe.member import Member


router = APIRouter()


@router.get("/tanggal/{id}/{tanggalawal}/{tanggalakhir}")
def get_dailybillbytanggal(
    id: int,
    tanggalawal: str,
    tanggalakhir: str,
    session: SessionDBKafeLogin
):
    query = (
        select(dailybill, Member.Nama)
        .join(Member, Member.ID == dailybill.ID)
        .where(dailybill.Tgl >= tanggalawal)
        .where(dailybill.Tgl <= tanggalakhir)
        .where(dailybill.ID == id)
    )

    results = session.exec(query).all()

    return {
        "status": "success",
        "data": [
            {
                **bill.model_dump(),
                "Nama": nama,
            }
            for bill, nama in results
        ],
    }


@router.get("/belumlunas/{id}/{tanggalawal}/{tanggalakhir}")
def get_dailybillbelumlunas(
    id: int,
    tanggalawal: str,
    tanggalakhir: str,
    session: SessionDBKafeLogin
):
    query = (
        select(dailybill, Member.Nama)
        .join(Member, Member.ID == dailybill.ID)
        .where(dailybill.Tgl >= tanggalawal)
        .where(dailybill.Tgl <= tanggalakhir)
        .where(dailybill.Lunas == 0)
        .where(dailybill.ID == id)
    )

    results = session.exec(query).all()

    return {
        "status": "success",
        "data": [
            {
                **bill.model_dump(),
                "Nama": nama,
            }
            for bill, nama in results
        ],
    }


@router.get("/belumlunas/{tanggalawal}/{tanggalakhir}")
def get_belumlunas(
    tanggalawal: str,
    tanggalakhir: str,
    session: SessionDBKafeLogin
):
    query = (
        select(dailybill, Member.Nama)
        .join(Member, Member.ID == dailybill.ID)
        .where(dailybill.Tgl >= tanggalawal)
        .where(dailybill.Tgl <= tanggalakhir)
        .where(dailybill.Lunas == 0)
    )

    results = session.exec(query).all()

    return {
        "status": "success",
        "data": [
            {
                **bill.model_dump(),
                "Nama": nama,
            }
            for bill, nama in results
        ],
    }


@router.get("/member/{nama}")
def get_member_by_nama(
    nama: str,
    session: SessionDBKafeLogin,
    current_user: dict = Depends(get_current_user)
):
    query = (
        select(Member.ID, Member.Nama)
        .where(Member.Nama.like(f"%{nama}%"))
        .where(Member.Active == 1)
    )

    results = session.exec(query).all()

    return {
        "status": "success",
        "data": [
            {
                "ID": item[0],
                "Nama": item[1],
            }
            for item in results
        ],
    }


@router.get("/all/tanggal/{tanggalawal}/{tanggalakhir}")
def get_all_dailybill(
    tanggalawal: str,
    tanggalakhir: str,
    session: SessionDBKafeLogin
):
    query = (
        select(dailybill, Member.Nama)
        .join(Member, Member.ID == dailybill.ID)
        .where(dailybill.Tgl >= tanggalawal)
        .where(dailybill.Tgl <= tanggalakhir)
    )

    results = session.exec(query).all()

    return {
        "status": "success",
        "data": [
            {
                **bill.model_dump(),
                "Nama": nama,
            }
            for bill, nama in results
        ],
    }


@router.get("/all/id/{id}/{tanggalawal}/{tanggalakhir}")
def get_dailybill_by_id(
    id: int,
    tanggalawal: str,
    tanggalakhir: str,
    session: SessionDBKafeLogin
):
    query = (
        select(dailybill, Member.Nama)
        .join(Member, Member.ID == dailybill.ID)
        .where(dailybill.Tgl >= tanggalawal)
        .where(dailybill.Tgl <= tanggalakhir)
        .where(dailybill.ID == id)
    )

    results = session.exec(query).all()

    return {
        "status": "success",
        "data": [
            {
                **bill.model_dump(),
                "Nama": nama,
            }
            for bill, nama in results
        ],
    }


@router.get("/all/belumlunas/id/{id}/{tanggalawal}/{tanggalakhir}")
def get_dailybill_belumlunas_by_id(
    id: int,
    tanggalawal: str,
    tanggalakhir: str,
    session: SessionDBKafeLogin
):
    query = (
        select(dailybill, Member.Nama)
        .join(Member, Member.ID == dailybill.ID)
        .where(dailybill.Tgl >= tanggalawal)
        .where(dailybill.Tgl <= tanggalakhir)
        .where(dailybill.ID == id)
        .where(dailybill.Lunas == 0)
    )

    results = session.exec(query).all()

    return {
        "status": "success",
        "data": [
            {
                **bill.model_dump(),
                "Nama": nama,
            }
            for bill, nama in results
        ],
    }