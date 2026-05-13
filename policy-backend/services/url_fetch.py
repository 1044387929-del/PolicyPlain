"""抓取公开网页正文（SSRF 基础防护 + 长度限制）。"""

import ipaddress
from urllib.parse import urlparse

import anyio
import httpx
import trafilatura
from fastapi import HTTPException, status

from settings import settings


def assert_public_http_url(url: str) -> str:
    raw = (url or "").strip()
    if not raw:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="网址不能为空")
    if len(raw) > 2048:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="网址过长")

    p = urlparse(raw)
    if p.scheme not in ("http", "https"):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="仅支持 http 或 https 链接")
    host = (p.hostname or "").lower()
    if not host:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="网址无效")

    blocked = frozenset(
        {
            "localhost",
            "127.0.0.1",
            "0.0.0.0",
            "::1",
            "metadata.google.internal",
            "169.254.169.254",
        }
    )
    if host in blocked or host.endswith(".localhost"):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="不允许访问该主机")

    try:
        ip = ipaddress.ip_address(host)
        if ip.is_private or ip.is_loopback or ip.is_link_local:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="不允许访问内网或保留地址")
    except ValueError:
        pass

    return raw


async def fetch_html(url: str) -> tuple[bytes, str]:
    timeout = httpx.Timeout(settings.URL_FETCH_TIMEOUT_SECONDS)
    headers = {"User-Agent": "PolicyPlain/1.0 (+policy-plain)"}
    async with httpx.AsyncClient(
        timeout=timeout,
        follow_redirects=True,
        max_redirects=settings.URL_FETCH_MAX_REDIRECTS,
    ) as client:
        resp = await client.get(url, headers=headers)
        resp.raise_for_status()
        final = str(resp.url)
        body = resp.content[: settings.URL_FETCH_MAX_BYTES]
        return body, final


async def html_to_plain_text(html_bytes: bytes, page_url: str) -> str:
    html = html_bytes.decode("utf-8", errors="ignore")

    def _extract() -> str:
        t = trafilatura.extract(html, url=page_url, include_comments=False)
        if not t:
            t = trafilatura.extract(html, url=page_url, favor_recall=True)
        return (t or "").strip()

    return await anyio.to_thread.run_sync(_extract)
