"""After a deploy: the address serves this commit's page.

    python3 verify.py <address> <commit>

The address is one environment's own directory of the site, such as
https://matti.github.io/posse-demo/testaaja/, and its page is the one checked: not the site's
root, not another directory. The commit is asked for in the address's query, so that the host's
cache answers with the page just deployed, not an earlier copy. Exit status 0 when it does, 1
when not.

GitHub Pages reports a deployment done some seconds before every edge serves it: until then
the directory answers with the earlier page, or 404 when it is new. So the page is asked for
again until it is this commit's or the time is up (WAIT_SECONDS, three minutes); what is
reported in the end is the last answer.
"""

import sys
import time
import urllib.error
import urllib.request

WAIT_SECONDS = 180
ASK_EVERY_SECONDS = 3

import content


def url_of(address: str, commit: str) -> str:
    """The directory's page itself, asked for at this commit."""
    return f"{address.rstrip('/')}/?v={commit}"


def problems_of(url: str, commit: str) -> list[str]:
    """What is wrong with the page at the address now; nothing when it is this commit's."""
    try:
        with urllib.request.urlopen(url, timeout=30) as answer:
            page = answer.read().decode()
            status = answer.status
            served = answer.geturl()
    except urllib.error.HTTPError as error:
        return [f"answered {error.code}"]
    except urllib.error.URLError as error:
        return [f"did not answer: {error.reason}"]
    problems = []
    if status != 200:
        problems.append(f"answered {status}")
    if not served.startswith(url.split("?", 1)[0]):
        problems.append(f"was sent on to {served}, not its own directory")
    if '<html lang="fi">' not in page or content.COMPANY not in page:
        problems.append("is not the company's Finnish page")
    if f'<meta name="version" content="{commit}">' not in page:
        problems.append(f"is not commit {commit}'s page")
    return problems


def main(address: str, commit: str, wait_seconds: float = WAIT_SECONDS) -> int:
    url = url_of(address, commit)
    deadline = time.monotonic() + wait_seconds
    while True:
        problems = problems_of(url, commit)
        if not problems or time.monotonic() >= deadline:
            break
        time.sleep(ASK_EVERY_SECONDS)
    for problem in problems:
        print(f"{url} {problem}", file=sys.stderr)
    return 1 if problems else 0


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(__doc__, file=sys.stderr)
        sys.exit(2)
    sys.exit(main(sys.argv[1], sys.argv[2]))
