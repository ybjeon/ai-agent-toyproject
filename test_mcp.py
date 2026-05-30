import asyncio
import logging
from typing import Any

from langchain_core.callbacks import BaseCallbackHandler
from langchain.agents import create_agent
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_ollama import ChatOllama

# ── Config ────────────────────────────────────────────────────────
OLLAMA_BASE_URL = "http://localhost:11434"
MODEL = "qwen2.5:7b"
MCP_SERVER_URL = "http://localhost:8000/mcp" 

# ── Logger ────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


class ToolLogger(BaseCallbackHandler):
    def on_tool_start(self, serialized: dict, input_str: str, **kwargs: Any) -> None:
        name = serialized.get("name", "unknown")
        logger.info("[TOOL START] %s | input: %s", name, input_str)

    def on_tool_end(self, output: Any, **kwargs: Any) -> None:
        logger.info("[TOOL END]   output: %s", output)

    def on_tool_error(self, error: BaseException, **kwargs: Any) -> None:
        logger.error("[TOOL ERROR] %s", error)


# ── LLM ──────────────────────────────────────────────────────────
llm = ChatOllama(model=MODEL, base_url=OLLAMA_BASE_URL)


# ── Main ─────────────────────────────────────────────────────────
async def main(transport: str) -> None:
    if transport == "stdio":
        client = MultiServerMCPClient(
            {
                "example-server": {
                    "command": "python3",
                    "args": ["mcp_server.py", transport],
                    "transport": transport,
                }
            }
        )
    elif transport == "streamable-http":
        client = MultiServerMCPClient(
            {
                "example-server": {
                    "url": MCP_SERVER_URL,
                    "transport": transport,
                }
            }
        )
    else:
        raise ValueError(f"Unsupported transport: {transport}")

    tools = await client.get_tools()
    logger.info("Loaded %d tool(s) from MCP server: %s", len(tools), [t.name for t in tools])

    agent = create_agent(llm, tools)

    questions = [
        "What is 7 plus 15?",
        "Echo the message 'Hello from MCP!'",
    ]

    for q in questions:
        print(f"\n>>>>>>> User: {q}")
        result = await agent.ainvoke(
            {"messages": [("human", q)]},
            config={"callbacks": [ToolLogger()]},
        )
        answer = result["messages"][-1].content
        print(f"\n<<<<<<< Assistant: {answer}")
        print("─" * 50)


if __name__ == "__main__":
    import sys
    transport = sys.argv[1] if len(sys.argv) > 1 else "streamable-http"
    asyncio.run(main(transport))
