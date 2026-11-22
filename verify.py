"""After a deploy: the address serves this commit's page.

    python3 verify.py <address> <commit>

The address is one environment's own directory of the site, such as
https://matti.github.io/posse-demo/testaaja/, and its page is the one checked: not the site's
root, not another directory. The commit is asked for in the address's query, so that the host's
cache answers with the page just deployed, not an earlier copy. Exit status 0 when it does, 1
when not.
"""

import sys
import urllib.request

import content


def url_of(address: str, commit: str) -> str:
    """The directory's page itself, asked for at this commit."""
    return f"{address.rstrip('/')}/?v={commit}"


def main(address: str, commit: str) -> int:
    url = url_of(address, commit)
    with urllib.request.urlopen(url, timeout=30) as answer:
        page = answer.read().decode()
        status = answer.status
        served = answer.geturl()
    problems = []
    if status != 200:
        problems.append(f"answered {status}")
    if not served.startswith(url.split("?", 1)[0]):
        problems.append(f"was sent on to {served}, not its own directory")
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
