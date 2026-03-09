from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    meross_email: str = ""
    meross_password: str = ""
    meross_api_base_url: str = "https://iotx-eu.meross.com"
    cors_origins: list[str] = ["http://localhost:4200", "http://148.230.126.181"]
    data_dir: str = "data"
    shelly_scan_timeout: float = 1.5
    shelly_command_timeout: float = 3.0
    shelly_scan_workers: int = 50

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
