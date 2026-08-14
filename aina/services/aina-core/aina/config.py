"""Konfigurasjon.

Alle nøkler er valgfrie. Mangler en nøkkel skal den tilhørende konnektoren
melde seg av — ikke hindre oppstart. Se ../../docs/03-api-nokler.md.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Innstillinger(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # Kjerne
    aina_env: str = "dev"
    aina_host: str = "0.0.0.0"
    aina_port: int = 8080
    aina_data_dir: Path = Path("./data")
    aina_household_pack: Path = Path("./packs/husstand.yaml")
    aina_log_level: str = "INFO"
    aina_node_id: str = "node-01"

    # api.met.no avviser kall uten identifiserende User-Agent med kontaktinfo.
    aina_user_agent: str = "aina/0.1 (kontakt@example.com)"

    # Posisjon (fallback dersom husstandsprofilen ikke er lastet)
    aina_lat: float = 59.9139
    aina_lon: float = 10.7522
    aina_altitude: int = 20

    # Strøm
    tibber_token: str | None = None
    aina_prisomrade: str = "NO1"

    # Språkmodell
    ollama_url: str = "http://localhost:11434"
    aina_local_model: str = "qwen2.5:7b-instruct"
    aina_local_model_lav_effekt: str = "qwen2.5:3b-instruct"
    anthropic_api_key: str | None = None
    aina_cloud_model: str = "claude-sonnet-5"
    aina_cloud_allowed: bool = True

    # Enhetslag
    homeassistant_url: str | None = None
    homeassistant_token: str | None = None

    # Strømforsyning
    aina_batteri_oransje: float = 60.0
    aina_batteri_rod: float = 25.0

    # Nettverksovervåking
    aina_helsesjekk_verter: str = "1.1.1.1,9.9.9.9,api.met.no"
    aina_helsesjekk_intervall_s: int = 30

    @property
    def cache_sti(self) -> Path:
        return self.aina_data_dir / "cache.sqlite"

    @property
    def helsesjekk_verter(self) -> list[str]:
        return [v.strip() for v in self.aina_helsesjekk_verter.split(",") if v.strip()]


@lru_cache
def hent_innstillinger() -> Innstillinger:
    return Innstillinger()
