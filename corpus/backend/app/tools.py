"""Mocked business tools. The ad platform fails a set number of times to demo recovery."""
class ToolError(Exception):
    def __init__(self, tool: str):
        super().__init__(tool)
        self.tool = tool


class Tools:
    def __init__(self, ad_failures: int = 0):
        self.ad_failures_left = ad_failures

    async def call(self, tool: str, **kw) -> dict:
        if tool == "ad_platform":
            if self.ad_failures_left > 0:
                self.ad_failures_left -= 1
                raise ToolError(tool)
            return {"ok": True, "campaign_id": "CMP-1001", "spent": kw.get("amount", 0)}
        if tool == "email":
            return {"ok": True, "sent": 25}
        return {"ok": True}
