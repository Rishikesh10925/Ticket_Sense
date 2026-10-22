"""Week 11 security check: no public default JWT secret outside development."""

import pytest
from pydantic import ValidationError

from app.config import Settings

STRONG = "a3f9" * 16  # 64 characters


@pytest.mark.parametrize("secret", ["dev-only-insecure-secret-change-me", "changeme-generate-a-real-secret-per-above",
                                    "short"])
def test_production_refuses_a_weak_secret(secret):
    with pytest.raises(ValidationError, match="JWT_SECRET_KEY"):
        Settings(app_env="production", jwt_secret_key=secret)


def test_production_accepts_a_real_secret():
    assert Settings(app_env="production", jwt_secret_key=STRONG).jwt_secret_key == STRONG


@pytest.mark.parametrize("env", ["development", "test"])
def test_development_keeps_the_default(env):
    Settings(app_env=env, jwt_secret_key="dev-only-insecure-secret-change-me")
