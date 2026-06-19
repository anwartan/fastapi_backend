import os
import uuid
from fastapi import UploadFile
from fastapi.responses import FileResponse
from app.model.FileData import FileData
from app.services.media_service import MediaService
class FileService:

    UPLOAD_DIR = "uploads"

    @staticmethod
    async def massUpload(files: list[UploadFile]) -> list[FileData]:
        uploaded_files = []
        for file in files:
            file_data = await FileService.upload(file)
            uploaded_files.append(file_data)
        return uploaded_files

    @staticmethod
    async def upload(file: UploadFile):

        os.makedirs(FileService.UPLOAD_DIR, exist_ok=True)

        filename = FileService.generateFileName(file.filename)
        file_path = FileService.getFilePath(filename=filename)

        content = await file.read()

        size = len(content)
        print(f"File size in bytes: {size}")

        size_kb = round(size / 1024, 2)
        with open(file_path, "wb") as buffer:
            buffer.write(content)

        file_data = FileData(
            filetype=file.content_type,
            filename=filename,
            filesize=size_kb,
            filepath=file_path
        )

        return file_data
    @staticmethod
    def generateFileName(filename: str):

        ext = filename.split(".")[-1]

        unique_name = f"{uuid.uuid4()}.{ext}"

        return unique_name

    @staticmethod
    def download(filename: str):

        file_path = FileService.getFilePath(filename=filename)

        if not os.path.exists(file_path):
            return None

        return FileResponse(
            path=file_path,
            filename=filename,
        )
    
    @staticmethod
    def getFilePath(filename:str):
        return os.path.join(
            FileService.UPLOAD_DIR,
            filename,
        )