"""Hello World MCP Server."""

import asyncio
from mcp.server import Server
from mcp.types import Resource, Tool, TextContent
import mcp.server.stdio


# Create server instance
app = Server("fuzzy-bassoon")


@app.list_resources()
async def list_resources() -> list[Resource]:
    """List available resources."""
    return [
        Resource(
            uri="hello://world",
            name="Hello World",
            mimeType="text/plain",
            description="A simple hello world resource",
        )
    ]


@app.read_resource()
async def read_resource(uri: str) -> str:
    """Read a resource by URI."""
    if uri == "hello://world":
        return "Hello, World from MCP Server!"
    raise ValueError(f"Unknown resource: {uri}")


@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available tools."""
    return [
        Tool(
            name="greet",
            description="Greet someone by name",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Name of the person to greet",
                    }
                },
                "required": ["name"],
            },
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Handle tool calls."""
    if name == "greet":
        person_name = arguments.get("name", "World")
        return [
            TextContent(
                type="text",
                text=f"Hello, {person_name}! Welcome to the MCP server.",
            )
        ]
    raise ValueError(f"Unknown tool: {name}")


async def main():
    """Run the server."""
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options(),
        )


if __name__ == "__main__":
    asyncio.run(main())
