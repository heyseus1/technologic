from __future__ import annotations
# This line helps Python handle type hints more cleanly.
# Type hints are the things like -> str or -> dict[str, Any].
# You do not need to fully understand this yet.
# It is just a modern Python best practice.

import json
# json lets us read data from .json files like users.json.

import logging
# logging lets us send debug/info messages to the terminal safely.

from pathlib import Path
# Path helps us work with file paths in a clean cross-platform way.

from typing import Any
# Any is used when a function can return different kinds of data.

from mcp.server.fastmcp import FastMCP
# This imports FastMCP from the MCP Python SDK.
# FastMCP makes it easier to create an MCP server with tools, resources, and prompts.


# ------------------------------------------------------------
# LOGGING SETUP
# ------------------------------------------------------------

# This turns on logging so we can print useful debug info.
# Important:
# For MCP, we do NOT want to use normal print() to stdout in many cases,
# because MCP may use stdout for protocol messages.
# logging is safer than random print statements.
logging.basicConfig(level=logging.INFO)


# ------------------------------------------------------------
# CREATE THE MCP SERVER
# ------------------------------------------------------------

# This creates a new MCP server named "identity-ops".
# Think of this like creating the main app object.
mcp = FastMCP("identity-ops")


# ------------------------------------------------------------
# FIND THE DATA FOLDER
# ------------------------------------------------------------

# __file__ is the current Python file (server.py).
# .resolve() gives us the full absolute path.
# .parents[2] moves up folders from:
# src/mcp_identity_ops/server.py
# up to:
# mcp-identity-ops/
# Path.cwd() means "the folder I am currently running this program from"
# Since you are launching the MCP server from mcp-identity-ops,
# this should point to:
# /Users/matthewmorcaldi/Documents/Code/github/technologic/mcp-identity-ops
BASE_DIR = Path.cwd()

# This points to the data folder inside the current project folder
DATA_DIR = BASE_DIR / "data"
# This points to the data folder inside the project.


# ------------------------------------------------------------
# HELPER FUNCTION: LOAD JSON FILES
# ------------------------------------------------------------

def load_json(filename: str) -> Any:
    """
    Open a JSON file from the data folder and return its contents.

    Example:
        load_json("users.json")

    Why this function exists:
    - So we do not repeat the same file-reading code everywhere
    - Makes the main tools cleaner and easier to read
    """
    with open(DATA_DIR / filename, "r", encoding="utf-8") as f:
        return json.load(f)


# ------------------------------------------------------------
# HELPER FUNCTION: CLEAN UP EMAILS
# ------------------------------------------------------------

def normalize_email(email: str) -> str:
    """
    Clean up an email string by:
    - removing extra spaces
    - converting it to lowercase

    This helps prevent matching issues such as:
    ' Alice@Zoom.us ' vs 'alice@zoom.us'
    """
    return email.strip().lower()


# ------------------------------------------------------------
# MCP TOOL #1: LOOK UP A USER
# ------------------------------------------------------------

@mcp.tool()
def lookup_user(email: str) -> dict[str, Any]:
    """
    Look up a user in users.json by email address.

    Tools are like functions that an AI client can call.
    This one searches our mock user directory.
    """

    # Load all users from users.json
    users = load_json("users.json")

    # Clean the email the user passed in
    target = normalize_email(email)

    # Go through every user in the JSON file
    for user in users:
        # Compare the stored email to the email we are searching for
        if normalize_email(user["email"]) == target:
            return user

    # If we never found a match, return an error message
    return {"error": f"User not found: {email}"}


# ------------------------------------------------------------
# MCP TOOL #2: LIST A USER'S ROLES
# ------------------------------------------------------------

@mcp.tool()
def list_user_roles(email: str) -> dict[str, Any]:
    """
    Return the roles assigned to a user from assignments_current.json.

    This is useful for answering:
    'What access does this user currently have?'
    """

    # Load current RBAC assignments
    assignments = load_json("assignments_current.json")

    # Clean the email we are searching for
    target = normalize_email(email)

    # Build a set of roles for this user
    # A set removes duplicates automatically
    roles = sorted(
        {
            item["role"]
            for item in assignments
            if normalize_email(item["email"]) == target
        }
    )

    # If no roles were found, return a friendly response
    if not roles:
        return {"email": email, "roles": [], "message": "No roles found"}

    # Otherwise return the found roles
    return {"email": email, "roles": roles}


# ------------------------------------------------------------
# MCP TOOL #3: COMPARE CURRENT VS DESIRED RBAC
# ------------------------------------------------------------

@mcp.tool()
def compare_rbac_assignments() -> dict[str, Any]:
    """
    Compare current RBAC assignments to desired RBAC assignments.

    This answers:
    - What roles are being added?
    - What roles are being removed?

    This is similar to checking the difference between
    current state and future planned state.
    """

    # Load both files
    current = load_json("assignments_current.json")
    desired = load_json("assignments_desired.json")

    # Convert each list into a set of tuples:
    # (email, role)
    #
    # Why?
    # Because sets make it easy to compare differences.
    current_set = {
        (normalize_email(item["email"]), item["role"]) for item in current
    }

    desired_set = {
        (normalize_email(item["email"]), item["role"]) for item in desired
    }

    # Roles in desired but not current = added
    added = sorted(desired_set - current_set)

    # Roles in current but not desired = removed
    removed = sorted(current_set - desired_set)

    # Return the results in a readable dictionary
    return {
        "added": [{"email": email, "role": role} for email, role in added],
        "removed": [{"email": email, "role": role} for email, role in removed],
        "summary": {
            "added_count": len(added),
            "removed_count": len(removed),
        },
    }


# ------------------------------------------------------------
# MCP TOOL #4: EXPLAIN ROLE CHANGES FOR ONE USER
# ------------------------------------------------------------

@mcp.tool()
def explain_access_change(email: str) -> dict[str, Any]:
    """
    Compare one user's current roles to desired roles.

    This answers:
    - What roles does the user have now?
    - What roles will they have later?
    - What roles are gained?
    - What roles are lost?
    """

    # Clean the email
    target = normalize_email(email)

    # Load both assignment files
    current = load_json("assignments_current.json")
    desired = load_json("assignments_desired.json")

    # Gather current roles for this user
    current_roles = sorted(
        {
            item["role"]
            for item in current
            if normalize_email(item["email"]) == target
        }
    )

    # Gather desired roles for this user
    desired_roles = sorted(
        {
            item["role"]
            for item in desired
            if normalize_email(item["email"]) == target
        }
    )

    # Convert lists to sets so we can compare them easily
    current_set = set(current_roles)
    desired_set = set(desired_roles)

    # Roles present in desired but not current
    gained = sorted(desired_set - current_set)

    # Roles present in current but not desired
    lost = sorted(current_set - desired_set)

    # Return a clear summary
    return {
        "email": email,
        "current_roles": current_roles,
        "desired_roles": desired_roles,
        "gained_roles": gained,
        "lost_roles": lost,
    }


# ------------------------------------------------------------
# MCP RESOURCE #1: FULL USER DIRECTORY
# ------------------------------------------------------------

@mcp.resource("users://directory")
def users_directory() -> str:
    """
    Return the full users.json file as text.

    Resources are different from tools:
    - Tools usually perform an action or calculation
    - Resources expose data that the AI can read

    Here we are exposing the whole directory file.
    """
    return (DATA_DIR / "users.json").read_text(encoding="utf-8")


# ------------------------------------------------------------
# MCP RESOURCE #2: RBAC SNAPSHOT READER
# ------------------------------------------------------------

@mcp.resource("rbac://assignments/{snapshot}")
def rbac_assignments(snapshot: str) -> str:
    """
    Return an RBAC snapshot file as text.

    Valid snapshot values:
    - current
    - desired

    Example resource paths:
    - rbac://assignments/current
    - rbac://assignments/desired
    """

    # Only allow known snapshot names
    allowed = {"current", "desired"}

    # If the user passes something invalid, return an error as JSON text
    if snapshot not in allowed:
        return json.dumps(
            {"error": f"Invalid snapshot '{snapshot}'. Use one of: {sorted(allowed)}"},
            indent=2,
        )

    # Build the filename automatically
    filename = f"assignments_{snapshot}.json"

    # Return the file contents as text
    return (DATA_DIR / filename).read_text(encoding="utf-8")


# ------------------------------------------------------------
# MCP PROMPT #1: REUSABLE REVIEW PROMPT
# ------------------------------------------------------------

@mcp.prompt()
def review_rbac_change(change_summary: str) -> str:
    """
    Return a reusable text prompt for reviewing RBAC changes.

    Prompts are like templates.
    They help an AI client start with a structured instruction.
    """

    return f"""
Review the following RBAC change summary.

Focus on:
1. Least privilege concerns
2. Risk of over-provisioning
3. Any suspicious privilege escalation
4. Recommended rollback or approval notes

RBAC CHANGE SUMMARY:
{change_summary}
""".strip()


# ------------------------------------------------------------
# MAIN FUNCTION
# ------------------------------------------------------------

def main() -> None:
    """
    Start the MCP server.

    mcp.run() launches the server so clients can connect to it.
    """
    mcp.run()


# ------------------------------------------------------------
# RUN THE PROGRAM
# ------------------------------------------------------------

# This checks:
# "Is this file being run directly?"
#
# If yes, run main().
# If this file is only being imported by another Python file,
# do not automatically start the server.
if __name__ == "__main__":
    main()
