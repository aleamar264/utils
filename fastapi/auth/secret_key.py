from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class SecretKey(BaseSettings):
	secret_key: str = Field(..., description="Secret key from env file")
	model_config = SettingsConfigDict(env_file=".secret.env", env_file_encoding="utf-8")


secret_key = SecretKey()
