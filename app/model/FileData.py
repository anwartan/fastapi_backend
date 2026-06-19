

class FileData:
    filename:str
    filetype:str
    filesize:int
    filepath:str

    def __init__(self, filename, filetype,filesize,filepath):
        self.filename=filename
        self.filetype=filetype
        self.filesize=filesize
        self.filepath=filepath