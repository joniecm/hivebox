from version import VERSION
import sys


def print_version() -> None:
    """Print the app version from `version.py` then exit.

    Exits with code 0 on success, 1 on failure.
    """
    if not VERSION:
        print("", file=sys.stderr)
        sys.exit(1)

    print(VERSION)
    sys.exit(0)


if __name__ == "__main__":
    print_version()
