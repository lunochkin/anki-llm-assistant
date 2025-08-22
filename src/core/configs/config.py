"""
Configuration management for Anki LLM Assistant.

This module loads configuration from the specs directory and provides
a clean interface for accessing runtime settings.
"""

import os
import yaml
import pathlib
from dataclasses import dataclass
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


@dataclass(frozen=True)
class RuntimeConfig:
    """Runtime configuration loaded from implementation.yaml"""
    language: str
    framework: str
    agent_style: str
    model_env: str
    temperature: float
    max_tokens: int


@dataclass(frozen=True)
class AdapterConfig:
    """Adapter configuration for external services"""
    anki: str  # "anki_connect" or "mock"


@dataclass(frozen=True)
class InvariantsConfig:
    """Business rules and constraints loaded from invariants.yaml"""
    max_decks: int
    max_cards: int
    text_rules: list[str]


@dataclass(frozen=True)
class Config:
    """Main configuration container"""
    runtime: RuntimeConfig
    adapters: AdapterConfig
    invariants: InvariantsConfig
    
    @property
    def model_name(self) -> str:
        """Get the model name from environment variable"""
        return os.getenv(self.runtime.model_env, "gpt-4o-mini")
    
    @property
    def openai_api_key(self) -> Optional[str]:
        """Get OpenAI API key from environment"""
        return os.getenv("OPENAI_API_KEY")


class ConfigLoader:
    """Loads configuration from spec files"""
    
    def __init__(self, specs_dir: str = "specs"):
        self.specs_dir = pathlib.Path(specs_dir)
    
    def load_config(self) -> Config:
        """Load complete configuration from specs"""
        return Config(
            runtime=self._load_runtime_config(),
            adapters=self._load_adapter_config(),
            invariants=self._load_invariants_config()
        )
    
    def _load_runtime_config(self) -> RuntimeConfig:
        """Load runtime configuration from implementation.yaml"""
        impl_path = self.specs_dir / "implementation.yaml"
        
        if not impl_path.exists():
            raise FileNotFoundError(f"Implementation config not found: {impl_path}")
        
        with open(impl_path, 'r') as f:
            data = yaml.safe_load(f)
        
        runtime_data = data.get("runtime", {})
        
        return RuntimeConfig(
            language=runtime_data.get("language", "python"),
            framework=runtime_data.get("framework", "langchain"),
            agent_style=runtime_data.get("agent_style", "react"),
            model_env=runtime_data.get("model_env", "OPENAI_MODEL"),
            temperature=runtime_data.get("temperature", 0.0),
            max_tokens=runtime_data.get("max_tokens", 800)
        )
    
    def _load_adapter_config(self) -> AdapterConfig:
        """Load adapter configuration from implementation.yaml"""
        impl_path = self.specs_dir / "implementation.yaml"
        
        with open(impl_path, 'r') as f:
            data = yaml.safe_load(f)
        
        adapters_data = data.get("adapters", {})
        
        return AdapterConfig(
            anki=adapters_data.get("anki", "anki_connect")
        )
    
    def _load_invariants_config(self) -> InvariantsConfig:
        """Load business rules from invariants.yaml"""
        invariants_path = self.specs_dir / "invariants.yaml"
        
        if not invariants_path.exists():
            raise FileNotFoundError(f"Invariants config not found: {invariants_path}")
        
        with open(invariants_path, 'r') as f:
            data = yaml.safe_load(f)
        
        inv_data = data.get("inv", {})
        
        # Build text rules from invariants
        text_rules = [
            f"INV-READ-1: {inv_data['INV-READ-1']['desc'].replace('N', str(inv_data['INV-READ-1']['N']))}",
            f"INV-READ-2: {inv_data['INV-READ-2']['desc'].replace('M', str(inv_data['INV-READ-2']['M']))}",
            f"INV-READ-3: {inv_data['INV-READ-3']['desc']}",
            f"INV-READ-4: {inv_data['INV-READ-4']['desc']}"
        ]
        
        return InvariantsConfig(
            max_decks=inv_data["INV-READ-1"]["N"],
            max_cards=inv_data["INV-READ-2"]["M"],
            text_rules=text_rules
        )


def load_config(specs_dir: str = "specs") -> Config:
    """Convenience function to load configuration"""
    loader = ConfigLoader(specs_dir)
    return loader.load_config()


def get_default_config() -> Config:
    """Get configuration with default specs directory"""
    return load_config()


# Environment-specific configuration helpers
def is_development() -> bool:
    """Check if running in development mode"""
    return os.getenv("ENVIRONMENT", "development").lower() == "development"


def is_testing() -> bool:
    """Check if running in testing mode"""
    return os.getenv("ENVIRONMENT", "development").lower() == "testing"


def should_use_mock_anki() -> bool:
    """Check if should use mock Anki adapter"""
    return is_testing() or os.getenv("USE_MOCK_ANKI", "false").lower() == "true"
