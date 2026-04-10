class DocumentException(Exception):
    pass

class UnsupportedFileType(DocumentException):
    pass

class FileUploadError(DocumentException):
    pass

class DocumentNotFound(DocumentException):
    pass

class NotAllowedToDelete(DocumentException):
    pass

class AccessDenied(DocumentException):
    pass

class SomethingWentWrong(DocumentException):
    pass