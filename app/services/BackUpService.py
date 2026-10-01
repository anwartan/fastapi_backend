import os
import zipfile
import subprocess
from datetime import datetime


IMAGE_FOLDER = os.path.join(
    "uploads"
)

BACKUP_FOLDER = os.path.join(
    "backups"
)

MYSQL_USER = os.getenv("DATABASE_USER")
MYSQL_PASSWORD = os.getenv("DATABASE_PASSWORD")
MYSQL_HOST = os.getenv("DATABASE_HOST")
MYSQL_PORT = os.getenv("DATABASE_PORT")
MYSQL_DATABASE = os.getenv("DATABASE_NAME_KAFE")

MYSQL_DUMP_PATH = os.getenv("MYSQL_DUMP_PATH") or ""
BACKUP_COUNT = os.getenv("BACKUP_COUNT") or 20


def create_backup_folder():
    os.makedirs(
        BACKUP_FOLDER,
        exist_ok=True
    )

    timestamp = datetime.now().strftime(
        "%Y-%m-%d_%H-%M-%S"
    )

    return timestamp


def backup_mysql(sql_file):
    mysql_dump_full_path = os.path.join(
        MYSQL_DUMP_PATH,
        "mysqldump.exe"
    )

    if not os.path.isfile(
        mysql_dump_full_path
    ):
        raise FileNotFoundError(
            f"mysqldump.exe tidak ditemukan: "
            f"{mysql_dump_full_path}"
        )



    command = [
        mysql_dump_full_path,
        f"--user={MYSQL_USER}",
        f"--password={MYSQL_PASSWORD}",
        f"--host={MYSQL_HOST}",
        f"--port={MYSQL_PORT}",
        "--routines",
        "--triggers",
        "--events",
        MYSQL_DATABASE
    ]

    with open(
        sql_file,
        "w",
        encoding="utf-8"
    ) as file:

        result = subprocess.run(
            command,
            stdout=file,
            stderr=subprocess.PIPE,
            text=True
        )

    if result.returncode != 0:

        if os.path.exists(sql_file):
            os.remove(sql_file)

        raise RuntimeError(
            f"Backup MySQL gagal: {result.stderr}"
        )

    return sql_file


def create_backup_zip(timestamp):
    zip_file = os.path.join(
        BACKUP_FOLDER,
        f"backup_{timestamp}.zip"
    )

    sql_file = os.path.join(
        BACKUP_FOLDER,
        f"database_{timestamp}.sql"
    )

    backup_mysql(sql_file)

    if not os.path.isdir(IMAGE_FOLDER):
        raise FileNotFoundError(
            f"Folder gambar tidak ditemukan: "
            f"{IMAGE_FOLDER}"
        )

    with zipfile.ZipFile(
        zip_file,
        "w",
        compression=zipfile.ZIP_DEFLATED
    ) as zipf:

        zipf.write(
            sql_file,
            "database.sql"
        )

        for root, dirs, files in os.walk(
            IMAGE_FOLDER
        ):

            for file in files:

                file_path = os.path.join(
                    root,
                    file
                )

                relative_path = os.path.relpath(
                    file_path,
                    IMAGE_FOLDER
                )

                archive_path = os.path.join(
                    "images",
                    relative_path
                )

                zipf.write(
                    file_path,
                    archive_path
                )

    os.remove(sql_file)

    return zip_file


def trim_backups(limit=20):
    if not os.path.exists(BACKUP_FOLDER):
        return

    backups = [
        os.path.join(BACKUP_FOLDER, file)
        for file in os.listdir(BACKUP_FOLDER)
        if file.endswith(".zip")
    ]

    backups.sort(
        key=os.path.getmtime,
        reverse=True
    )

    for backup in backups[limit:]:
        os.remove(backup)

        print(
            f"Backup lama dihapus: {backup}"
        )



def run_backup():
    print("=== BACKUP START ===")

    try:
        timestamp = create_backup_folder()

        zip_file = create_backup_zip(
            timestamp
        )

        
        trim_backups(int(BACKUP_COUNT))

        print(
            f"Backup berhasil: {zip_file}"
        )

        return {
            "success": True,
            "file": zip_file
        }

    except Exception as e:

        print(
            f"=== BACKUP GAGAL === {e}"
        )

        return {
            "success": False,
            "error": str(e)
        }