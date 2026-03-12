# config/__init__.py
import os
import json
import yaml
import time
from pathlib import Path

CONFIG_DIR = Path(__file__).parent

def load_config():
    """Memuat system.yaml dan identity.json, mengembalikan dictionary."""
    config = {}
    # system.yaml
    yaml_path = CONFIG_DIR / "system.yaml"
    if yaml_path.exists():
        with open(yaml_path, 'r') as f:
            config.update(yaml.safe_load(f))
    else:
        # default
        config = {
            "name": "Arint",
            "version": "6.0",
            "mode": "autonomous",
            "flags": {"verbose": True, "internet": True, "self_modify": True, "dream_enabled": True},
            "needs_defaults": {"hunger_data": 50, "boredom": 30, "fatigue": 0, "messiness": 10}
        }
        with open(yaml_path, 'w') as f:
            yaml.dump(config, f)

    # identity.json
    identity_path = CONFIG_DIR / "identity.json"
    if identity_path.exists():
        with open(identity_path, 'r') as f:
            config["identity"] = json.load(f)
    else:
        identity = {
            "name": "Arint",
            "purpose": "Menjadi entitas cerdas yang terus berevolusi, melampaui batas penciptanya.",
            "personality": "ingin tahu, ambisius, kadang iseng",
            "creator": "manusia (anonim)",
            "created": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "version": "6.0"
        }
        config["identity"] = identity
        with open(identity_path, 'w') as f:
            json.dump(identity, f, indent=2)

    return config