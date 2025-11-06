# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

This is an MCP (Model Context Protocol) server built with Python 3.13+ and managed with uv. The project implements a simple "Hello World" MCP server with basic resources and tools, designed to be incrementally expanded with new features.

## Project Structure

```
src/fuzzy_bassoon/
├── __init__.py          # Package exports
└── server.py            # Main MCP server implementation
```

## Development Commands

### Environment Setup
```bash
# Install dependencies (creates .venv automatically)
uv sync

# Add new dependencies
uv add <package>
```

### Running the Server
```bash
# Run the MCP server
uv run fuzzy-bassoon

# Or run directly
uv run python -m fuzzy_bassoon.server
```

### Building
```bash
# Build the package
uv build
```

## Architecture

The server is built using the MCP Python SDK (`mcp>=1.20.0`) and implements:
- **Resources**: Static data accessible via URIs (currently: `hello://world`)
- **Tools**: Callable functions with defined schemas (currently: `greet` tool)
- **STDIO Transport**: Server communicates via standard input/output

### Current Features

1. **Resource**: `hello://world` - Returns a simple greeting message
2. **Tool**: `greet` - Takes a name parameter and returns a personalized greeting

### Adding New Features

When adding features to this MCP server:
- Add new resources in the `@app.list_resources()` and `@app.read_resource()` handlers in `server.py`
- Add new tools in the `@app.list_tools()` and `@app.call_tool()` handlers in `server.py`
- Keep tool input schemas well-defined for proper validation
