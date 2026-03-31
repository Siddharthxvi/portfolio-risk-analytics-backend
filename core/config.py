from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://root:password@localhost:5432/portfolio_risk_db"

    class Config:
        env_file = ".env"

settings = Settings()
