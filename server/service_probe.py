import json
import sys
from urllib.request import urlopen


EXPECTED_NAME = "第N人格"
EXPECTED_VERSION = "0.3.1"


def main():
    base_url = sys.argv[1].rstrip("/")
    try:
        with urlopen(f"{base_url}/version", timeout=2) as response:
            payload = json.load(response)
    except Exception:
        print(json.dumps({"status": "unavailable"}))
        return 1

    if (
        payload.get("name") == EXPECTED_NAME
        and payload.get("version") == EXPECTED_VERSION
    ):
        print(
            json.dumps(
                {
                    "status": "current",
                    "name": EXPECTED_NAME,
                    "version": EXPECTED_VERSION,
                },
                ensure_ascii=False,
            )
        )
        return 0

    print(
        json.dumps(
            {
                "status": "conflict",
                "name": payload.get("name"),
                "version": payload.get("version"),
            },
            ensure_ascii=False,
        )
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
