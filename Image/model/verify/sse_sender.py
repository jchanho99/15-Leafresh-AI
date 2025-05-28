import json
import os
import httpx

class SSESender:
    def __init__(self, base_url_env: str = "CALLBACK_URL"):
        self.base_url_template = os.getenv(base_url_env)


    async def send(self, verification_id: int, result_dict: dict):
        url = self.base_url_template.format(verificationId=verification_id)
        headers = {
            "Content-Type": "text/event-stream"
        }

        sse_message = f"data: {json.dumps(result_dict)}\n\n"

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(url, content=sse_message, headers=headers)
                print(f"[SSE 전송 완료] {url} → {response.status_code}")
        except Exception as e:
            print(f"[SSE 전송 실패] {e}")

