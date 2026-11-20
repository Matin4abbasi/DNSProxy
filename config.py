import ipaddress
import os
import sys
from domains import is_valid_domain, normalize

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, "config.txt")
REQUIRED_KEYS = [
    "upstream_ip",
    "upstream_port",
    "sinkhole_ip",
    "proxy_ip",
    "ad_list_file",
    "sanction_list_file",
]
class ConfigError(Exception):
    pass

def _resolve_path(path: str) -> str:
    return path if os.path.isabs(path) else os.path.join(BASE_DIR, path)


def _read_key_values(path: str) -> dict:
    if not os.path.isfile(path):
        raise ConfigError(f"file not found: {path}")
    values = {}
    with open(path, encoding="utf-8") as f:
        for lineno, raw in enumerate(f, 1):
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                raise ConfigError(f"line {lineno} is not in key=value form: {line}")
            key, value = line.split("=", 1)
            values[key.strip()] = value.strip()
    return values


def _ipv4(key: str, value: str) -> str:
    try:
        return str(ipaddress.IPv4Address(value))
    except ValueError:
        raise ConfigError(f"{key} must be a valid IPv4 address, got '{value}'")


def _number(key: str, value: str, kind=int, minimum=0, maximum=None):
    try:
        number = kind(value)
    except ValueError:
        raise ConfigError(f"{key} must be a number, got '{value}'")
    if number < minimum or (maximum is not None and number > maximum):
        raise ConfigError(f"{key} is out of range: {value}")
    return number


def load_config(path: str = CONFIG_PATH) -> dict:
    """Return a validated config dict. Raises ConfigError on any problem."""
    raw = _read_key_values(path)

    for key in REQUIRED_KEYS:
        if key not in raw or raw[key] == "":
            raise ConfigError(f"missing required key: {key}")

    cfg = {
        "upstream_ip": _ipv4("upstream_ip", raw["upstream_ip"]),
        "upstream_port": _number("upstream_port", raw["upstream_port"], int, 1, 65535),
        "upstream_timeout_sec": _number(
            "upstream_timeout_sec", raw.get("upstream_timeout_sec", "2"), float, 0.001
        ),
        "sinkhole_ip": _ipv4("sinkhole_ip", raw["sinkhole_ip"]),
        "proxy_ip": _ipv4("proxy_ip", raw["proxy_ip"]),
        "local_ttl": _number("local_ttl", raw.get("local_ttl", "60"), int, 0),
        "ad_list_file": _resolve_path(raw["ad_list_file"]),
        "sanction_list_file": _resolve_path(raw["sanction_list_file"]),
    }

    cache_value = raw.get("cache_enabled", "true").lower()
    if cache_value not in ("true", "false"):
        raise ConfigError(f"cache_enabled must be true or false, got '{raw['cache_enabled']}'")
    cfg["cache_enabled"] = cache_value == "true"

    for key in ("ad_list_file", "sanction_list_file"):
        if not os.path.isfile(cfg[key]):
            raise ConfigError(f"{key}: file not found: {cfg[key]}")

    return cfg

def load_list(path: str) -> set:
    entries = set()
    with open(path, encoding="utf-8") as f:
        for lineno, raw in enumerate(f, 1):
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            if not is_valid_domain(line):
                print(f"Warning: bad line {lineno} in {os.path.basename(path)}: {line}")
                continue
            entries.add(normalize(line))
    return entries

def load_config_or_exit() -> dict:
    try:
        return load_config()
    except ConfigError as e:
        print(f"Config error: {e}")
        sys.exit(1)
