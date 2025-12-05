from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    jaketodo_api_token: str
    database_path: str = "./data/todos.db"


settings = Settings()
