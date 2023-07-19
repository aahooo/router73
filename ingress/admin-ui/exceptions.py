class PortalException(Exception):
    message = ""
    code = 400

class CommandExecException(PortalException):
    def __init__(self, stdout: bytes, stderr: bytes, code: int) -> None:
        super().__init__()
        self.message = f"Failed to execute command:\n  stdout:{stdout}\n  stderr:{stderr}\n  exit code:{code}"
        self.code = 500


class UserDoesNotExist(PortalException):
    def __init__(self, user: str) -> None:
        super().__init__()
        self.message = f"User {user} doesn't exist"
        self.code = 404

class UserAlreadyExists(PortalException):
    def __init__(self, user: str) -> None:
        super().__init__()
        self.message = f"User {user} already exists"
        self.code = 409

class InvalidUserName(PortalException):
    def __init__(self) -> None:
        super().__init__()
        self.message = "Username could only contain alphanumeric characters, `_` and `-`"
        self.code = 406

