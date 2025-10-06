import os
from dataclasses import dataclass
from typing import Dict

from dotenv import load_dotenv


@dataclass(frozen=True)
class Counts:
    count_100b: int
    count_10kb: int
    count_1mb: int
    count_10mb: int

    @classmethod
    def from_env(cls) -> "Counts":
        return cls(
            count_100b=int(os.getenv("COUNT_100B", "10000")),
            count_10kb=int(os.getenv("COUNT_10KB", "1000")),
            count_1mb=int(os.getenv("COUNT_1MB", "100")),
            count_10mb=int(os.getenv("COUNT_10MB", "10")),
        )

    def to_map(self) -> Dict[str, int]:
        return {
            "f_100B.bin": self.count_100b,
            "f_10KB.bin": self.count_10kb,
            "f_1MB.bin": self.count_1mb,
            "f_10MB.bin": self.count_10mb,
        }


@dataclass(frozen=True)
class Endpoints:
    broker_host: str
    broker_port: int
    mqtt_topic_prefix: str

    coap_host: str
    coap_port: int

    http_host: str
    http_port: int

    @classmethod
    def from_env(cls) -> "Endpoints":
        return cls(
            broker_host=os.getenv("BROKER_HOST", "127.0.0.1"),
            broker_port=int(os.getenv("BROKER_PORT", "1883")),
            mqtt_topic_prefix=os.getenv("MQTT_TOPIC_PREFIX", "hw3/files"),
            coap_host=os.getenv("COAP_HOST", "127.0.0.1"),
            coap_port=int(os.getenv("COAP_PORT", "5683")),
            http_host=os.getenv("HTTP_HOST", "0.0.0.0"),
            http_port=int(os.getenv("HTTP_PORT", "8080")),
        )


@dataclass(frozen=True)
class Settings:
    endpoints: Endpoints
    counts: Counts
    log_dir: str

    @classmethod
    def load(cls) -> "Settings":
        load_dotenv(override=False)
        return cls(
            endpoints=Endpoints.from_env(),
            counts=Counts.from_env(),
            log_dir=os.getenv("LOG_DIR", "logs"),
        )
