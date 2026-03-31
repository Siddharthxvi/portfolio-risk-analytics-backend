from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://risk_platform_gcga_user:olxEJdFWKnzf1gG7zoCiqZ0qKrEtrk6V@dpg-d75mgrgule4c73ctlj0g-a.singapore-postgres.render.com/risk_platform_gcga?sslmode=require"

    class Config:
        env_file = ".env"

settings = Settings()
