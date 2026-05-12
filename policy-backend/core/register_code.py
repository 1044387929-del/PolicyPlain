"""注册验证码 HMAC（与 DB 中 code_hash 比对）。"""

import hashlib
import hmac

from settings import settings


def register_code_hmac_hex(email: str, code: str) -> str:
    key = settings.JWT_SECRET_KEY.encode("utf-8")
    msg = f"{email}:{code}".encode("utf-8")
    return hmac.new(key, msg, hashlib.sha256).hexdigest()


def verify_register_code(email: str, code: str, code_hash: str) -> bool:
    if not code_hash or len(code) != 6:
        return False
    try:
        return hmac.compare_digest(register_code_hmac_hex(email, code), code_hash)
    except Exception:
        return False
