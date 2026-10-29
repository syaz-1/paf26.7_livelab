"""Exercise the real SDK client and HTTPS server with an ephemeral test CA.

Only storage/service collectors are synthetic; no mounts or systemd changes.
"""
import asyncio
from datetime import datetime, timedelta, timezone
import ipaddress
from pathlib import Path
import socket
import ssl
import sys
import tempfile
import threading
import time
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID
import httpx
import uvicorn

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import collectors
import check_mcp
from server import build_app


class TLSTests(unittest.TestCase):
    def test_https_client_auth_and_five_tools(self):
        with tempfile.TemporaryDirectory(prefix="paf-lab-tls-") as directory:
            directory = Path(directory)
            key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
            name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "localhost")])
            now = datetime.now(timezone.utc)
            cert = (x509.CertificateBuilder().subject_name(name).issuer_name(name)
                    .public_key(key.public_key()).serial_number(x509.random_serial_number())
                    .not_valid_before(now - timedelta(minutes=1)).not_valid_after(now + timedelta(hours=1))
                    .add_extension(x509.SubjectAlternativeName([
                        x509.IPAddress(ipaddress.ip_address("127.0.0.1"))]), critical=False)
                    .add_extension(x509.BasicConstraints(ca=True, path_length=0), critical=True)
                    .sign(key, hashes.SHA256()))
            cert_file, key_file, token_file = [directory / name for name in ("ca.pem", "key.pem", "token")]
            cert_file.write_bytes(cert.public_bytes(serialization.Encoding.PEM))
            key_file.write_bytes(key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8,
                                                    serialization.NoEncryption()))
            key_file.chmod(0o600)
            token_file.write_text("test-only-" + "x" * 48)
            token_file.chmod(0o600)
            with socket.socket() as listener:
                listener.bind(("127.0.0.1", 0))
                port = listener.getsockname()[1]
                url = f"https://127.0.0.1:{port}/mcp"
                server = uvicorn.Server(uvicorn.Config(
                    build_app(token_file.read_text(), url), host="127.0.0.1", port=port,
                    ssl_certfile=str(cert_file), ssl_keyfile=str(key_file),
                    access_log=False, log_level="warning"))
                thread = threading.Thread(target=server.run, kwargs={"sockets": [listener]}, daemon=True)
                thread.start()
                try:
                    deadline = time.monotonic() + 5
                    while not server.started and thread.is_alive() and time.monotonic() < deadline:
                        time.sleep(0.01)
                    self.assertTrue(server.started, "HTTPS test server failed to start")
                    with self.assertRaises(httpx.ConnectError):
                        httpx.post(url, json={}, timeout=2, trust_env=False)
                    fake = collectors.evidence(lambda out: out["data"].update({"synthetic": True}))
                    with patch.object(collectors, "filesystem_usage", return_value=fake), \
                         patch.object(collectors, "demo_service_status", return_value=fake):
                        asyncio.run(check_mcp.check(SimpleNamespace(
                            url=url, token_file=str(token_file), ca_file=str(cert_file))))
                finally:
                    server.should_exit = True
                    thread.join(timeout=10)
                    self.assertFalse(thread.is_alive(), "HTTPS test server did not shut down")


if __name__ == "__main__":
    unittest.main()
