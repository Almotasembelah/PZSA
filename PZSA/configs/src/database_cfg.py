from pydantic_settings import BaseSettings

class Settings(BaseSettings):

    DATABASE_URL: str
    VIOLATION_FRAME_FOLDER_PATH: str

    class Config:
        env_file = '.env'

def get_settings():
    return Settings()