"""After a deploy: the address serves this commit's page.

    python3 verify.py <address> <commit>

The commit is asked for in the address's query, so that the host's cache answers with the page
just deployed, not an earlier copy. Exit status 0 when it does, 1 when not.
"""

import sys
import urllib.request

import content


def main(address: str, commit: str) -> int:
    url = f"{address.rstrip('/')}/?v={commit}"
    with urllib.request.urlopen(url, timeout=30) as answer:
        page = answer.read().decode()
        status = answer.status
    problems = []
    if status != 200:
        problems.append(f"answered {status}")
    if '<html lang="fi">' not in page or content.COMPANY not in page:
        problems.append("is not the company's Finnish page")
    if f'<meta name="version" content="{commit}">' not in page:
        problems.append(f"is not commit {commit}'s page")
    for problem in problems:
        print(f"{url} {problem}", file=sys.stderr)
    return 1 if problems else 0


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(__doc__, file=sys.stderr)
        sys.exit(2)
    sys.exit(main(sys.argv[1], sys.argv[2]))
