"""Test bootstrap: set dummy provider env vars BEFORE app modules import.

`app.config.Settings()` requires the provider keys at import time. Setting them
here (env vars outrank the .env file in pydantic-settings) lets the suite import
the app and run hermetically — provider clients are lazy and mocked in tests, so
these dummy values are never used to make real calls.
"""

import os

os.environ.setdefault("ANTHROPIC_API_KEY", "test-anthropic-key")
os.environ.setdefault("VOYAGE_API_KEY", "test-voyage-key")
os.environ.setdefault("SUPABASE_URL", "https://test.supabase.co")
os.environ.setdefault("SUPABASE_SERVICE_ROLE_KEY", "test-service-role-key")
