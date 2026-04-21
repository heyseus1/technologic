import argparse
import asyncio
import json
from typing import Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


# ------------------------------------------------------------
# HELPER FUNCTION: PRETTY PRINT JSON
# ------------------------------------------------------------

def print_json(data: Any) -> None:
    """
    Print Python data in a clean JSON format.

    indent=2 makes it easier for humans to read.
    """
    print(json.dumps(data, indent=2))


# ------------------------------------------------------------
# HELPER FUNCTION: CLEAN TOOL OUTPUT
# ------------------------------------------------------------

def extract_tool_output(result: Any) -> Any:
    """
    MCP tool results can come back in a few forms.

    We prefer structuredContent if it exists because it is already
    parsed into a Python dictionary.

    If structuredContent does not exist, fall back to the text content.
    """
    if hasattr(result, "structuredContent") and result.structuredContent is not None:
        return result.structuredContent

    if hasattr(result, "content") and result.content:
        first_item = result.content[0]

        if hasattr(first_item, "text"):
            try:
                # Try to parse the returned text as JSON
                return json.loads(first_item.text)
            except Exception:
                # If it is not valid JSON, just return the raw text
                return first_item.text

    return {"message": "No usable tool output returned"}


# ------------------------------------------------------------
# HELPER FUNCTION: CLEAN RESOURCE OUTPUT
# ------------------------------------------------------------

def extract_resource_output(result: Any) -> Any:
    """
    MCP resource results usually come back in result.contents.

    We read the first content block and try to parse it as JSON.
    """
    if hasattr(result, "contents") and result.contents:
        first_item = result.contents[0]

        if hasattr(first_item, "text"):
            try:
                return json.loads(first_item.text)
            except Exception:
                return first_item.text

    return {"message": "No usable resource output returned"}


# ------------------------------------------------------------
# ARGUMENT PARSER
# ------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    """
    Create the command-line parser.

    Subcommands make the CLI feel like a real tool.
    """
    parser = argparse.ArgumentParser(
        description="Simple MCP CLI client for the identity-ops server"
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    # lookup_user <email>
    lookup_user_parser = subparsers.add_parser(
        "lookup_user",
        help="Look up a user by email"
    )
    lookup_user_parser.add_argument("email", help="Email address to search for")

    # list_user_roles <email>
    list_roles_parser = subparsers.add_parser(
        "list_user_roles",
        help="List current roles for a user"
    )
    list_roles_parser.add_argument("email", help="Email address to search for")

    # compare_rbac_assignments
    subparsers.add_parser(
        "compare_rbac_assignments",
        help="Compare current vs desired RBAC assignments"
    )

    # explain_access_change <email>
    explain_parser = subparsers.add_parser(
        "explain_access_change",
        help="Explain role changes for a specific user"
    )
    explain_parser.add_argument("email", help="Email address to search for")

    # read_resource <uri>
    read_resource_parser = subparsers.add_parser(
        "read_resource",
        help="Read a resource URI from the MCP server"
    )
    read_resource_parser.add_argument("uri", help="Resource URI, for example users://directory")

    # list_tools
    subparsers.add_parser(
        "list_tools",
        help="List available MCP tools"
    )

    # list_resources
    subparsers.add_parser(
        "list_resources",
        help="List available MCP resources"
    )

    return parser


# ------------------------------------------------------------
# MAIN MCP CLIENT LOGIC
# ------------------------------------------------------------

async def run_client(args: argparse.Namespace) -> None:
    """
    Connect to the local MCP server over stdio and run the requested command.
    """

    # This tells the client how to launch the MCP server.
    # We are using uv to run the local Python file.
    server_params = StdioServerParameters(
        command="uv",
        args=[
            "run",
            "server.py",
        ],
    )

    # Start the stdio connection to the server
    async with stdio_client(server_params) as (read_stream, write_stream):
        # Create a client session so we can call tools/resources
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()

            # ----------------------------------------------------
            # TOOL: lookup_user
            # ----------------------------------------------------
            if args.command == "lookup_user":
                result = await session.call_tool(
                    "lookup_user",
                    {"email": args.email}
                )
                print_json(extract_tool_output(result))
                return

            # ----------------------------------------------------
            # TOOL: list_user_roles
            # ----------------------------------------------------
            if args.command == "list_user_roles":
                result = await session.call_tool(
                    "list_user_roles",
                    {"email": args.email}
                )
                print_json(extract_tool_output(result))
                return

            # ----------------------------------------------------
            # TOOL: compare_rbac_assignments
            # ----------------------------------------------------
            if args.command == "compare_rbac_assignments":
                result = await session.call_tool(
                    "compare_rbac_assignments",
                    {}
                )
                print_json(extract_tool_output(result))
                return

            # ----------------------------------------------------
            # TOOL: explain_access_change
            # ----------------------------------------------------
            if args.command == "explain_access_change":
                result = await session.call_tool(
                    "explain_access_change",
                    {"email": args.email}
                )
                print_json(extract_tool_output(result))
                return

            # ----------------------------------------------------
            # RESOURCE: read_resource
            # ----------------------------------------------------
            if args.command == "read_resource":
                result = await session.read_resource(args.uri)
                print_json(extract_resource_output(result))
                return

            # ----------------------------------------------------
            # LIST TOOLS
            # ----------------------------------------------------
            if args.command == "list_tools":
                result = await session.list_tools()

                tools = []
                for tool in result.tools:
                    tools.append(
                        {
                            "name": tool.name,
                            "description": tool.description,
                        }
                    )

                print_json(tools)
                return

            # ----------------------------------------------------
            # LIST RESOURCES
            # ----------------------------------------------------
            if args.command == "list_resources":
                result = await session.list_resources()

                resources = []
                for resource in result.resources:
                    resources.append(
                        {
                            "name": resource.name,
                            "uri": str(resource.uri),
                            "description": resource.description,
                        }
                    )

                print_json(resources)
                return


# ------------------------------------------------------------
# PROGRAM ENTRY POINT
# ------------------------------------------------------------

def main() -> None:
    """
    Parse command-line arguments, then run the async client.
    """
    parser = build_parser()
    args = parser.parse_args()
    asyncio.run(run_client(args))


if __name__ == "__main__":
    main()