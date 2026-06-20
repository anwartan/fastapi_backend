from sqlalchemy.orm import Session
from app.model.kafe.Media import Media
from app.model.FileData import FileData
from fastapi import Depends
from app.database import SessionDBKafe

class MediaService:

    def __init__(self, session : SessionDBKafe ):
        self.session = session

    def create(self, order:FileData, subject:str, id: int):
        new_media = Media(
            FileName=order.filename,
            FileType=order.filetype,
            FileSize=order.filesize,
            FilePath=order.filepath,
            SubjectId=id,
            SubjectType=subject,
        )

        self.session.add(new_media)
        self.session.commit()
        
    
    def createMany (self, orders: list[FileData], subject: str, id: int):
        for i in orders:
            self.create(i, subject, id)
        
    def deleteByFileName(self, fileName: str):
        media = self.session.query(Media).filter(Media.FileName == fileName).first()
        if media:
            self.session.delete(media)
            self.session.commit()
            return True
        return False



        