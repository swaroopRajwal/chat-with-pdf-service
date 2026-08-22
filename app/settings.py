from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str
    embedding_model: str
    vector_dimensions: int
    chunk_size: int
    chunk_overlap: int
    llm_model: str
    llm_api_base: str
    llm_api_key: str
    llm_temperature: int
    llm_max_tokens: int


settings = Settings()
