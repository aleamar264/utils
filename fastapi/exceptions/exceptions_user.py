from typing import Callable

from fastapi.requests import Request
from fastapi.responses import JSONResponse


class UserApiError(Exception):
	"""base exception for all user api errors"""

	def __init__(
		self, message: str = "service is unavailable", name: str = "UserApi"
	) -> None:
		self.message = message
		self.name = name
		super().__init__(self.message, self.name)


class LoginError(UserApiError):
	"""Error during login"""

	pass


class EntityDoesNotExistError(UserApiError):
	"""Entity does not exist"""

	pass


class EntityAlreadyExistsError(UserApiError):
	"""Entity already exists"""

	pass


class InvalidTokenError(UserApiError):
	"""Invalid token"""

	pass


class InvalidCredentialsError(UserApiError):
	"""Invalid credentials"""

	pass


def create_exception_handler(
	status_code: int, initial_detail: str
) -> Callable[[Request, UserApiError], JSONResponse]:
	detail = {"message": initial_detail}

	async def exception_handler(_: Request, exc: UserApiError) -> JSONResponse:
		if exc.message:
			detail["message"] = exc.message
		if exc.name:
			detail["name"] = exc.name
		return JSONResponse(
			status_code=status_code, content={"detail": detail["message"]}
		)

	return exception_handler
