class DocumentException(Exception):
    pass

class UnsupportedFileType(DocumentException):
    pass

class FileUploadError(DocumentException):
    pass

class DocumentNotFound(DocumentException):
    pass