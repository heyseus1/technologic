#!/usr/bin/env python3

"""
fetch_user.py

CLI tool to retrieve a user from the Okta Admin API using OAuth 2.0
Client Credentials with private_key_jwt authentication (JWK).

Design goals:
- Fully agnostic (no hardcoded org/tenant)
- CLI-friendly (supports args + interactive prompt)
- Does not assume any specific user attributes (prints raw JSON)
- Clear, human-readable errors
"""

import argparse          # Parses command-line args and provides --help automatically
import json              # Pretty-prints JSON output
import os                # Reads environment variables (keeps org details out of code)
import sys               # Allows clean exit codes for automation
from typing import Any   # Type hinting for readability (not required but helpful)
from urllib.parse import quote  # Properly URL-encodes the login when used in a URL path

import requests          # HTTP client used to call Okta APIs

from jwk_auth_module import okta_jwk_authentication  # Your existing auth module


def get_okta_domain() -> str:
    """
    Returns the Okta domain from env var OKTA_DOMAIN.

    Why?
    - Keeps the script portable across different Okta orgs
    - Prevents hardcoding org-specific details (professional + safer for GitHub)

    Example:
        export OKTA_DOMAIN="dev-123456.okta.com"
    """
    domain = os.environ.get("OKTA_DOMAIN")
    if not domain:
        raise RuntimeError(
            "OKTA_DOMAIN environment variable not set.\n"
            "Example:\n"
            "  export OKTA_DOMAIN='dev-123456.okta.com'"
        )
    return domain.strip()


def fetch_user(login: str) -> Any:
    """
    Fetches a user from Okta by login (email/username).

    Important:
    - Okta recommends URL-encoding the login when it is used in the URL path.
    - Logins containing '/' can be problematic in path routing; Okta docs recommend
      fetching by user ID instead if '/' is present.

    Returns:
    - Raw JSON response from Okta (dict), without assuming any attributes.
    """
    if "/" in login:
        raise ValueError(
            "Login contains '/'. Okta docs recommend fetching these users by ID "
            "due to URL escaping/routing issues."
        )

    domain = get_okta_domain()

    # URL-encode login because it is inserted into a URL *path segment*
    encoded_login = quote(login, safe="")

    url = f"https://{domain}/api/v1/users/{encoded_login}"

    # Get OAuth access token (your JWK-based auth flow)
    token = okta_jwk_authentication().okta_token()
    if not token:
        raise RuntimeError("Failed to obtain Okta access token (empty token).")

    headers = {
        "Accept": "application/json",
        "Authorization": f"Bearer {token}",
    }

    # timeout prevents the request from hanging indefinitely
    response = requests.get(url, headers=headers, timeout=20)

    # Raises requests.HTTPError for non-2xx responses (401/403/404/429/etc.)
    response.raise_for_status()

    # Return raw JSON (agnostic: we do not parse attributes)
    return response.json()


def main() -> int:
    """
    CLI entrypoint.

    Why argparse?
    - Allows calling from CLI like:
        python fetch_user.py user@example.com
    - Provides built-in --help output
    - Makes it easy to add future flags without rewriting code

    Returns an exit code:
    - 0 = success
    - 1 = request failed
    - 2 = bad input / configuration
    """
    parser = argparse.ArgumentParser(
        description="Fetch an Okta user by login (email) and print raw JSON."
    )
    parser.add_argument(
        "login",
        nargs="?",  # Optional positional argument
        help="User login/email (e.g. user@example.com). If omitted, you'll be prompted.",
    )
    args = parser.parse_args()

    # If no CLI arg provided, fall back to interactive prompt
    login = args.login or input("Enter user email/login: ").strip()

    if not login:
        print("Error: login/email is required.", file=sys.stderr)
        return 2

    try:
        data = fetch_user(login)
        print(json.dumps(data, indent=2, sort_keys=True))
        return 0

    except requests.HTTPError as e:
        # Non-2xx HTTP response
        status = e.response.status_code if e.response else "?"
        print(f"HTTP error ({status}).", file=sys.stderr)

        # Print raw response body (may be JSON or text)
        if e.response is not None and e.response.text:
            print(e.response.text, file=sys.stderr)

        return 1

    except (requests.RequestException,) as e:
        # Network issues, timeouts, connection errors, etc.
        print(f"Network error: {e}", file=sys.stderr)
        return 1

    except (ValueError, RuntimeError) as e:
        # Configuration or known validation errors
        print(f"Error: {e}", file=sys.stderr)
        return 2

    except Exception as e:
        # Catch-all so the CLI doesn't dump a stack trace in normal usage
        print(f"Unexpected error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())