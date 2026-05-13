"""与 hr-backend/core/ocr.py 对齐：调用飞桨 AI Studio PaddleOCR 云端任务 API。"""

from __future__ import annotations

import asyncio
import json
import logging
import os
from typing import Any

import httpx

from settings import settings

logger = logging.getLogger(__name__)


class PaddleOcr:
    """使用 aistudio PaddleOCR v2 jobs API；需配置 PADDLE_OCR_ACCESS_TOKEN。"""

    def __init__(self) -> None:
        self.job_url = (settings.PADDLE_OCR_JOB_URL or "").strip() or (
            "https://paddleocr.aistudio-app.com/api/v2/ocr/jobs"
        )
        self.access_token = settings.PADDLE_OCR_ACCESS_TOKEN.strip()
        self.model_name = (settings.PADDLE_OCR_MODEL_NAME or "").strip() or "PaddleOCR-VL-1.5"
        self.headers = {
            "Authorization": f"bearer {self.access_token}",
        }
        self.optional_payload: dict[str, Any] = {
            "useDocOrientationClassify": False,
            "useDocUnwarping": False,
            "useChartRecognition": False,
        }

    async def create_job(self, file_path: str) -> str:
        if not self.access_token:
            raise ValueError("未配置 PADDLE_OCR_ACCESS_TOKEN")

        if file_path.startswith("http"):
            self.headers["Content-Type"] = "application/json"
            payload = {
                "fileUrl": file_path,
                "model": self.model_name,
                "optionalPayload": self.optional_payload,
            }
            async with httpx.AsyncClient(timeout=httpx.Timeout(120.0)) as client:
                job_resp = await client.post(self.job_url, json=payload, headers=self.headers)
        else:
            if not os.path.isfile(file_path):
                raise ValueError(f"文件不存在：{file_path}")
            data = {
                "model": self.model_name,
                "optionalPayload": json.dumps(self.optional_payload),
            }
            async with httpx.AsyncClient(timeout=httpx.Timeout(120.0)) as client:
                with open(file_path, "rb") as fp:
                    files = {"file": fp}
                    job_resp = await client.post(self.job_url, headers=self.headers, data=data, files=files)

        if job_resp.status_code != 200:
            logger.error("PaddleOCR 创建任务失败：%s", job_resp.text)
            raise ValueError(f"PaddleOCR 创建任务失败：{job_resp.text}")

        body = job_resp.json()
        job_id = body.get("data", {}).get("jobId")
        if not job_id:
            raise ValueError(f"PaddleOCR 响应无 jobId：{body!r}")
        return str(job_id)

    async def poll_for_state(self, job_id: str) -> str:
        url = f"{self.job_url.rstrip('/')}/{job_id}"
        while True:
            async with httpx.AsyncClient(timeout=httpx.Timeout(120.0)) as client:
                job_result_response = await client.get(url, headers=self.headers)
            if job_result_response.status_code != 200:
                raise ValueError(f"查询任务状态失败：{job_result_response.text}")

            data = job_result_response.json().get("data") or {}
            state = data.get("state")
            if state == "pending":
                logger.info("PaddleOCR job %s pending…", job_id)
            elif state == "running":
                prog = data.get("extractProgress") or {}
                total = prog.get("totalPages")
                done = prog.get("extractedPages")
                if total is not None and done is not None:
                    logger.info("PaddleOCR job %s running %s/%s", job_id, done, total)
                else:
                    logger.info("PaddleOCR job %s running…", job_id)
            elif state == "done":
                json_url = (data.get("resultUrl") or {}).get("jsonUrl")
                if not json_url:
                    raise ValueError("PaddleOCR 完成但无 resultUrl.jsonUrl")
                return str(json_url)
            elif state == "failed":
                err = data.get("errorMsg") or "unknown"
                raise ValueError(f"PaddleOCR 任务失败：{err}")
            else:
                logger.warning("PaddleOCR job %s unknown state: %s", job_id, state)

            await asyncio.sleep(2)

    async def fetch_parsed_contents(self, jsonl_url: str) -> list[str]:
        contents: list[str] = []
        async with httpx.AsyncClient(timeout=httpx.Timeout(120.0)) as client:
            jsonl_response = await client.get(jsonl_url)
        if jsonl_response.status_code != 200:
            raise ValueError(f"拉取识别结果失败：{jsonl_response.text}")

        for line in jsonl_response.text.strip().split("\n"):
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
                result = obj.get("result") or {}
                for res in result.get("layoutParsingResults") or []:
                    md = res.get("markdown")
                    if isinstance(md, dict) and md.get("text"):
                        contents.append(str(md["text"]))
            except (json.JSONDecodeError, KeyError, TypeError) as e:
                logger.warning("跳过异常 jsonl 行：%s", e)
        return contents

    async def extract_text_from_file(self, file_path: str) -> str:
        job_id = await self.create_job(file_path)
        jsonl_url = await self.poll_for_state(job_id)
        parts = await self.fetch_parsed_contents(jsonl_url)
        return "\n\n".join(parts).strip()
