"""
Runtime server settings for the Stock BI entrypoint.
"""
import socket

from shared.stock_core.config import get_env, get_int
from shared.stock_core.env import bootstrap_project_env


bootstrap_project_env(__file__)


DEFAULT_API_PORT = 8000
DEFAULT_API_PORT_SCAN_COUNT = 20


def _resolve_port_scan_count() -> int:
    return max(get_int("API_PORT_SCAN_COUNT", DEFAULT_API_PORT_SCAN_COUNT), 1)


def _normalize_bind_host(host: str) -> str:
    if host == "localhost":
        return "127.0.0.1"
    return host


def _is_port_available(host: str, port: int) -> bool:
    bind_host = _normalize_bind_host(host)
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.bind((bind_host, port))
        except OSError:
            return False
    return True


def resolve_server_host_port() -> tuple[str, int]:
    host = get_env("API_HOST", "0.0.0.0")
    base_port = get_int("API_PORT", DEFAULT_API_PORT)

    if _is_port_available(host, base_port):
        return host, base_port

    for port_offset in range(1, _resolve_port_scan_count()):
        candidate_port = base_port + port_offset
        if _is_port_available(host, candidate_port):
            return host, candidate_port

    raise RuntimeError(
        f"No available port found for host={host} starting at port={base_port} "
        f"within scan_count={_resolve_port_scan_count()}"
    )


def build_local_urls(port: int) -> tuple[str, str]:
    base_url = f"http://localhost:{port}"
    return base_url, f"{base_url}/api/docs"
