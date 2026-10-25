import pytest
from app.core.config import Settings
from app.seed.seed_data import seed_database

# ==============================================================================
# Production Configuration Hardening Tests (SIH PS 26262 Remediation 3)
# ==============================================================================

VALID_PROD_KEY = "a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6"
VALID_PROD_DB = "postgresql+psycopg2://app_prod:StrongPassword987!@db-prod.internal:5432/reguflow_prod"

def test_production_settings_rejects_default_development_secret_key():
    """Proves that production startup rejects the publicly visible default signing key."""
    with pytest.raises(ValueError) as excinfo:
        Settings(
            ENVIRONMENT="production",
            DEBUG=False,
            DEMO_MODE=False,
            SECRET_KEY="supersecret_dev_key_change_in_production_reguflow360",
            DATABASE_URL=VALID_PROD_DB
        )
    assert "Production safety violation" in str(excinfo.value)
    assert "known development default" in str(excinfo.value)

def test_production_settings_rejects_short_or_empty_secret_key():
    """Proves that production startup rejects empty or short secret keys (< 32 chars)."""
    # Empty key
    with pytest.raises(ValueError) as exc_empty:
        Settings(
            ENVIRONMENT="production",
            DEBUG=False,
            DEMO_MODE=False,
            SECRET_KEY="",
            DATABASE_URL=VALID_PROD_DB
        )
    assert "SECRET_KEY must not be empty" in str(exc_empty.value)

    # Too short (< 32 chars)
    with pytest.raises(ValueError) as exc_short:
        Settings(
            ENVIRONMENT="production",
            DEBUG=False,
            DEMO_MODE=False,
            SECRET_KEY="short_key_under_32_characters",
            DATABASE_URL=VALID_PROD_DB
        )
    assert "too short" in str(exc_short.value)

def test_production_settings_rejects_debug_mode_enabled():
    """Proves that production startup fails closed if DEBUG is True."""
    with pytest.raises(ValueError) as excinfo:
        Settings(
            ENVIRONMENT="production",
            DEBUG=True,
            DEMO_MODE=False,
            SECRET_KEY=VALID_PROD_KEY,
            DATABASE_URL=VALID_PROD_DB
        )
    assert "DEBUG mode must be False in production" in str(excinfo.value)

def test_production_settings_rejects_demo_mode_enabled():
    """Proves that production startup fails closed if DEMO_MODE is True."""
    with pytest.raises(ValueError) as excinfo:
        Settings(
            ENVIRONMENT="production",
            DEBUG=False,
            DEMO_MODE=True,
            SECRET_KEY=VALID_PROD_KEY,
            DATABASE_URL=VALID_PROD_DB
        )
    assert "DEMO_MODE must be False in production" in str(excinfo.value)

def test_production_settings_rejects_sqlite_database():
    """Proves that production startup rejects SQLite database configuration."""
    with pytest.raises(ValueError) as excinfo:
        Settings(
            ENVIRONMENT="production",
            DEBUG=False,
            DEMO_MODE=False,
            SECRET_KEY=VALID_PROD_KEY,
            DATABASE_URL="sqlite:///./reguflow.db"
        )
    assert "SQLite is prohibited in production" in str(excinfo.value)

def test_production_settings_rejects_default_development_db_password():
    """Proves that production startup rejects known development database passwords."""
    with pytest.raises(ValueError) as excinfo:
        Settings(
            ENVIRONMENT="production",
            DEBUG=False,
            DEMO_MODE=False,
            SECRET_KEY=VALID_PROD_KEY,
            DATABASE_URL="postgresql+psycopg2://reguflow:reguflow_secret@db:5432/reguflow360"
        )
    assert "DATABASE_URL contains known default development credentials" in str(excinfo.value)

def test_production_settings_accepts_valid_secure_configuration():
    """Proves that a compliant production configuration instantiates cleanly."""
    prod_settings = Settings(
        ENVIRONMENT="production",
        DEBUG=False,
        DEMO_MODE=False,
        SECRET_KEY=VALID_PROD_KEY,
        DATABASE_URL=VALID_PROD_DB
    )
    assert prod_settings.is_production is True
    assert prod_settings.is_demo_allowed is False
    assert prod_settings.DEBUG is False

def test_development_settings_preserves_frictionless_local_demo():
    """Proves that the local development setup still functions with documented development settings."""
    dev_settings = Settings(
        ENVIRONMENT="development",
        DEBUG=True,
        DEMO_MODE=True,
        SECRET_KEY="supersecret_dev_key_change_in_production_reguflow360",
        DATABASE_URL="sqlite:///./reguflow.db"
    )
    assert dev_settings.is_production is False
    assert dev_settings.is_demo_allowed is True
    assert dev_settings.DEBUG is True

def test_production_seed_database_prohibited():
    """Proves that automatic or accidental seed operations are blocked in production."""
    from app.core import config
    original_env = config.settings.ENVIRONMENT
    try:
        config.settings.ENVIRONMENT = "production"
        with pytest.raises(RuntimeError) as excinfo:
            seed_database()
        assert "Production safety violation" in str(excinfo.value)
        assert "Automatic seeding of shared demo identities" in str(excinfo.value)
    finally:
        config.settings.ENVIRONMENT = original_env

def test_production_settings_error_does_not_leak_secrets():
    """Proves that production validation errors do not print the secret key value."""
    test_secret = "dev_key_super_secret_secret_1234567890"
    with pytest.raises(ValueError) as excinfo:
        Settings(
            ENVIRONMENT="production",
            DEBUG=False,
            DEMO_MODE=False,
            SECRET_KEY=test_secret,
            DATABASE_URL=VALID_PROD_DB
        )
    error_message = str(excinfo.value)
    assert test_secret not in error_message
