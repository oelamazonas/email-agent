"""
Configuration centralisée pour Email Agent AI
"""
from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    """Configuration de l'application"""
    
    # Application
    ENVIRONMENT: str = "production"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    SECRET_KEY: str
    ENCRYPTION_KEY: str
    
    # Database
    DATABASE_URL: str
    
    # Redis
    REDIS_URL: str
    REDIS_PASSWORD: Optional[str] = None
    
    # Ollama
    OLLAMA_HOST: str = "http://ollama:11434"
    OLLAMA_MODEL: str = "mistral"
    OLLAMA_TIMEOUT: int = 120  # seconds
    
    # API Options (fallback)
    USE_ANTHROPIC_FALLBACK: bool = False
    ANTHROPIC_API_KEY: Optional[str] = None
    ANTHROPIC_MODEL: str = "claude-haiku-4-5-20251001"
    
    # Email Processing
    EMAIL_POLL_INTERVAL: int = 5  # minutes
    PROCESSING_MODE: str = "suggest"  # suggest ou auto
    QUARANTINE_DAYS: int = 7
    MAX_EMAIL_SIZE_MB: int = 25
    
    # Admin
    ADMIN_EMAIL: str = "admin@example.com"
    ADMIN_PASSWORD: str = "changeme"
    
    # Backup
    BACKUP_DIR: str = "/var/backups/email-agent"
    BACKUP_RETENTION_DAYS: int = 30
    
    # Security
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    
    # OAuth (optionnel)
    GOOGLE_CLIENT_ID: Optional[str] = None
    GOOGLE_CLIENT_SECRET: Optional[str] = None
    GOOGLE_REDIRECT_URI: Optional[str] = None
    
    MICROSOFT_CLIENT_ID: Optional[str] = None
    MICROSOFT_CLIENT_SECRET: Optional[str] = None
    MICROSOFT_REDIRECT_URI: Optional[str] = None
    MICROSOFT_TENANT_ID: str = "common"  # common for multi-tenant, or specific tenant ID
    
    # Monitoring
    SENTRY_DSN: Optional[str] = None
    PROMETHEUS_ENABLED: bool = False
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"


# Instance globale des settings
settings = Settings()


# Configuration de logging basée sur les settings
def configure_logging():
    """Configure le système de logging"""
    import logging
    
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('/app/logs/email-agent.log') if os.path.exists('/app/logs') else logging.NullHandler()
        ]
    )
    
    # Configurer Sentry si disponible
    if settings.SENTRY_DSN:
        try:
            import sentry_sdk
            sentry_sdk.init(
                dsn=settings.SENTRY_DSN,
                environment=settings.ENVIRONMENT,
                traces_sample_rate=0.1 if settings.ENVIRONMENT == "production" else 1.0
            )
        except ImportError:
            logging.warning("Sentry SDK not installed")


# Initialiser le logging au démarrage
configure_logging()
