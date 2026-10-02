"""Interactive Microsoft Graph smoke test for local development."""

from .auth import get_access_token
from .graph import GraphClient, GraphError


def main() -> int:
    try:
        get_access_token()
        client = GraphClient()
        profile = client.get("/me", params={"$select": "id,displayName,userPrincipalName"})
        messages = client.get(
            "/me/messages",
            params={"$select": "id,subject,receivedDateTime", "$top": 1},
        )
    except Exception as exc:
        print(f"Microsoft Graph verification failed: {exc}")
        return 1
    print("Microsoft login and Graph verification succeeded.")
    print(f"User: {profile.get('displayName') or profile.get('userPrincipalName') or 'authenticated user'}")
    print(f"Message endpoint returned {len(messages.get('value', []))} message(s) in the sample.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
