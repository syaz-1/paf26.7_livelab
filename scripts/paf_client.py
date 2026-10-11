"""Small authenticated Agent Factory client; never logs secrets or cookies."""
import base64
import hashlib
import http.client
import json
from pathlib import Path
import ssl
from http.cookies import SimpleCookie
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
KNOWN_CERT_SHA256 = '1408131f5612db54194d6b26e2b100a4a743ccc1594cadf0d49665f3a4d9bc53'


def read_env():
    result = {}
    for line in (ROOT / '.env').read_text().splitlines():
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        if line.startswith('export '):
            line = line[7:]
        key, sep, value = line.partition('=')
        if sep:
            value = value.strip()
            if len(value) >= 2 and value[0] == value[-1] and value[0] in ('"', "'"):
                value = value[1:-1]
            result[key.strip()] = value
    return result


class Client:
    def __init__(self):
        env = read_env()
        url = urlsplit(env['agent_factory_url'])
        if url.scheme != 'https' or url.username or url.password:
            raise ValueError('Expected an HTTPS URL without embedded credentials.')
        self.host, self.port = url.hostname, url.port or 443
        self.origin = f'https://{url.netloc}'
        self.username = env['agent_factory_username']
        self.password = env['agent_factory_password']
        self.cookies = {}

    def request(self, method, path, data=None, login=False, timeout=180, raw_response=False):
        if not path.startswith('/agentFactory/') or '\r' in path or '\n' in path:
            raise ValueError('Request must remain within Agent Factory.')
        # Training server certificate explicitly trusted by the user on 2026-10-11.
        # Keep checking the exact fingerprint before transmitting credentials.
        connection = http.client.HTTPSConnection(self.host, self.port,
            context=ssl._create_unverified_context(), timeout=timeout)
        connection.connect()
        fingerprint = hashlib.sha256(connection.sock.getpeercert(binary_form=True)).hexdigest()
        if fingerprint != KNOWN_CERT_SHA256:
            connection.close()
            raise RuntimeError('Server certificate changed; re-verify before sending credentials.')
        headers = {'Origin': self.origin, 'Referer': self.origin + '/agentFactory/'}
        if login:
            token = base64.b64encode((self.username + ':' + self.password).encode()).decode()
            headers['Authorization'] = 'Basic ' + token
        if self.cookies:
            headers['Cookie'] = '; '.join(k + '=' + v for k, v in self.cookies.items())
        body = None
        if data is not None:
            body = json.dumps(data).encode()
            headers['Content-Type'] = 'application/json'
        try:
            connection.request(method, path, body, headers)
            response = connection.getresponse()
            for key, value in response.getheaders():
                if key.lower() == 'set-cookie':
                    cookie = SimpleCookie()
                    cookie.load(value)
                    for name, morsel in cookie.items():
                        self.cookies[name] = morsel.value
            raw = response.read()
            if raw_response:
                return response.status, raw
            try:
                result = json.loads(raw)
            except (ValueError, UnicodeDecodeError):
                result = raw.decode('utf-8', 'replace')
            return response.status, result
        finally:
            connection.close()

    def login(self):
        status, result = self.request('GET', '/agentFactory/v1/loginValidation', login=True)
        if status != 200 or not self.cookies:
            raise RuntimeError(f'Login failed (HTTP {status}); response withheld to protect credentials.')
        return result

    def redact(self, value):
        text = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False)
        for secret in [self.password, self.username] + list(self.cookies.values()):
            if secret:
                text = text.replace(secret, '[REDACTED]')
        return text
