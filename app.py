"""Posse Demo Oy's website: one page in Finnish, served by Python's standard library alone.

    python3 app.py [port]          serve on 127.0.0.1; port 0 (the default) takes a free one.
                                   The first line printed is the port, once it is listening.
    python3 app.py --build <dir>   write the pages as static files, for hosting
"""

import html
import http.server
import json
import os
import pathlib
import sys

import content as c

STYLE = """
:root { color-scheme: light dark; --accent: #1f6f50; }
body { font: 18px/1.5 system-ui, sans-serif; margin: 0; }
header, main, footer { max-width: 44rem; margin: 0 auto; padding: 1rem 1.25rem; }
header { border-bottom: 4px solid var(--accent); }
h1 { margin: 0; font-size: 1.8rem; }
.tagline { margin: 0; }
section { margin: 2rem 0; }
table { border-collapse: collapse; width: 100%; }
td { padding: .35rem 0; border-bottom: 1px solid #8884; }
td:last-child { text-align: right; }
.price { white-space: nowrap; font-weight: 600; }
"""


def version() -> str:
    """Which commit the page is of: the one the deploy workflow builds, or "local"."""
    return os.environ.get("GITHUB_SHA", "local")


def _shell(title: str, body: str) -> str:
    version_ = html.escape(version(), quote=True)
    return f"""<!doctype html>
<html lang="fi">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="version" content="{version_}">
<title>{html.escape(title)}</title>
<style>{STYLE}</style>
</head>
<body>
{body}
</body>
</html>
"""


def student_price(price: str) -> str:
    """The listed price ("59 euroa") less the student discount, in euros with a decimal comma."""
    amount, unit = price.split(" ", 1)
    cents = int(amount) * 100 * (100 - c.STUDENT_PERCENT)
    cents = (cents + 50) // 100
    return f"{cents // 100},{cents % 100:02d} {unit}"


def home() -> str:
    e = html.escape
    services = "\n".join(
        f'<tr><td><strong>{e(name)}</strong><br>{e(what)}</td><td class="price">{e(price)}'
        f'<br><span class="student">{e(c.STUDENT_LABEL)} {e(student_price(price))}</span></td></tr>'
        for name, what, price in c.SERVICES
    )
    hours = "\n".join(f"<tr><td>{e(day)}</td><td>{e(time)}</td></tr>" for day, time in c.HOURS)
    body = f"""<header>
<h1>{e(c.COMPANY)}</h1>
<p class="tagline">{e(c.TAGLINE)}</p>
</header>
<main>
<p>{e(c.LEAD)}</p>
<section id="palvelut">
<h2>{e(c.SERVICES_HEADING)}</h2>
<table>
{services}
</table>
<p class="student-note">{e(c.STUDENT_NOTE)}</p>
</section>
<section id="aukioloajat">
<h2>{e(c.HOURS_HEADING)}</h2>
<table>
{hours}
</table>
</section>
<section id="yhteystiedot">
<h2>{e(c.CONTACT_HEADING)}</h2>
<p>{e(c.ADDRESS)}<br>
<a href="tel:{e(c.PHONE.replace(" ", ""), quote=True)}">{e(c.PHONE)}</a><br>
<a href="mailto:{e(c.EMAIL, quote=True)}">{e(c.EMAIL)}</a></p>
</section>
</main>"""
    return _shell(f"{c.COMPANY}: {c.TAGLINE}", body)


def not_found() -> str:
    e = html.escape
    body = f"""<main>
<h1>{e(c.NOT_FOUND_TITLE)}</h1>
<p>{e(c.NOT_FOUND_LEAD)}</p>
<p><a href="./">{e(c.BACK_HOME)}</a></p>
</main>"""
    return _shell(c.NOT_FOUND_TITLE, body)


def answer(path: str) -> tuple[int, str, bytes]:
    """(status, content type, body) for a GET of the path."""
    path = path.split("?", 1)[0]
    if path in ("/", "/index.html"):
        return 200, "text/html; charset=utf-8", home().encode()
    if path == "/health":
        return 200, "application/json", json.dumps({"ok": True}).encode()
    return 404, "text/html; charset=utf-8", not_found().encode()


class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        status, kind, body = answer(self.path)
        self.send_response(status)
        self.send_header("Content-Type", kind)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *_args) -> None:
        pass


def server(port: int = 0) -> http.server.ThreadingHTTPServer:
    """A server bound to 127.0.0.1 and listening; port 0 takes a free one."""
    return http.server.ThreadingHTTPServer(("127.0.0.1", port), Handler)


def build(target: pathlib.Path) -> None:
    """The pages as static files: index.html and the host's own 404.html."""
    target.mkdir(parents=True, exist_ok=True)
    (target / "index.html").write_text(home(), encoding="utf-8")
    (target / "404.html").write_text(not_found(), encoding="utf-8")


def main(args: list[str]) -> int:
    if args[:1] == ["--build"] and len(args) == 2:
        build(pathlib.Path(args[1]))
        return 0
    if len(args) > 1 or (args and not args[0].isdigit()):
        print(__doc__, file=sys.stderr)
        return 2
    running = server(int(args[0]) if args else 0)
    print(running.server_address[1], flush=True)
    running.serve_forever()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
