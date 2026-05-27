from mcp.server.fastmcp import FastMCP

mcp = FastMCP("example-server")


@mcp.tool()
def add(a: int, b: int) -> int:
    """
    Add two numbers.

    Args:
        a: first number
        b: second number
    """
    return a + b


@mcp.tool()
def echo(message: str) -> str:
    """
    Echo the given message.

    Args:
        message: text to echo
    """
    return f"echo: {message}"


@mcp.resource("config://app")
def get_config() -> str:
    """
    Return example app configuration.
    """
    return "mode=dev\nversion=1.0.0"


if __name__ == "__main__":
    mcp.run(transport="stdio")