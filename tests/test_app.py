"""The site's own tests: what each address answers, the static copy, and a real server."""

import pathlib
import sys
import tempfile
import threading
import unittest
import urllib.error
import urllib.request

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

import app  # noqa: E402
import content  # noqa: E402
import verify  # noqa: E402


class Pages(unittest.TestCase):
    def test_the_front_page_is_finnish_and_says_everything_a_visitor_needs(self):
        status, kind, body = app.answer("/")
        page = body.decode()
        self.assertEqual((status, kind), (200, "text/html; charset=utf-8"))
        self.assertIn('<html lang="fi">', page)
        for text in (content.COMPANY, content.TAGLINE, content.ADDRESS, content.PHONE, content.EMAIL):
            self.assertIn(text, page)
        for name, _, price in content.SERVICES:
            self.assertIn(name, page)
            self.assertIn(price, page)
        for day, time in content.HOURS:
            self.assertIn(f"<td>{day}</td><td>{time}</td>", page)

    def test_the_phone_number_can_be_called_from_the_page(self):
        page = app.answer("/")[2].decode()
        self.assertIn('href="tel:+358401234567"', page)

    def test_text_is_escaped(self):
        original = content.TAGLINE
        content.TAGLINE = "<script>x</script>"
        try:
            page = app.home()
        finally:
            content.TAGLINE = original
        self.assertNotIn("<script>", page)
        self.assertIn("&lt;script&gt;", page)

    def test_health_answers_for_the_monitor(self):
        self.assertEqual(app.answer("/health"), (200, "application/json", b'{"ok": true}'))

    def test_an_unknown_address_gets_a_finnish_page(self):
        status, _, body = app.answer("/ei-ole")
        self.assertEqual(status, 404)
        self.assertIn(content.NOT_FOUND_TITLE, body.decode())

    def test_the_static_copy_is_the_same_as_the_served_page(self):
        with tempfile.TemporaryDirectory() as target:
            app.build(pathlib.Path(target))
            built = pathlib.Path(target, "index.html").read_text(encoding="utf-8")
            missing = pathlib.Path(target, "404.html").read_text(encoding="utf-8")
        self.assertEqual(built, app.answer("/")[2].decode())
        self.assertEqual(missing, app.answer("/ei-ole")[2].decode())


class Verify(unittest.TestCase):
    def test_a_directory_of_the_site_is_checked_at_its_own_address(self):
        for address in (
            "https://matti.github.io/posse-demo/testaaja/",
            "https://matti.github.io/posse-demo/testaaja",
        ):
            self.assertEqual(
                verify.url_of(address, "abc"),
                "https://matti.github.io/posse-demo/testaaja/?v=abc",
            )


class Served(unittest.TestCase):
    def test_a_real_server_answers_on_a_free_port(self):
        running = app.server(0)
        thread = threading.Thread(target=running.serve_forever, daemon=True)
        thread.start()
        try:
            base = f"http://127.0.0.1:{running.server_address[1]}"
            with urllib.request.urlopen(base + "/", timeout=10) as answer:
                self.assertEqual(answer.status, 200)
                self.assertIn(content.COMPANY, answer.read().decode())
            with self.assertRaises(urllib.error.HTTPError) as missing:
                urllib.request.urlopen(base + "/ei-ole", timeout=10)
            self.assertEqual(missing.exception.code, 404)
            # What the deploy workflow asks after a deploy: this commit's page, or a failure.
            self.assertEqual(verify.main(base, app.version()), 0)
            self.assertEqual(verify.main(base, "not-" + app.version()), 1)
        finally:
            running.shutdown()
            running.server_close()
            thread.join()


if __name__ == "__main__":
    unittest.main()
