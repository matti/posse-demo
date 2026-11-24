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

    def test_the_opening_hours_are_9_17_on_weekdays_and_10_14_on_saturdays(self):
        page = app.answer("/")[2].decode()
        self.assertIn("<td>Maanantai-perjantai</td><td>9-17</td>", page)
        self.assertIn("<td>Lauantai</td><td>10-14</td>", page)
        self.assertIn("<td>Sunnuntai</td><td>suljettu</td>", page)
        self.assertNotIn("10-18", page)
        self.assertNotIn("10-16", page)
        self.assertNotIn("10-15", page)

    def test_the_winter_service_is_listed_with_its_price_and_three_tasks(self):
        page = app.answer("/")[2].decode()
        self.assertIn("Talvihuolto", page)
        self.assertIn("49 euroa", page)
        for task in ("talvikunnostus", "nastarenkaiden vaihto", "ketjun voitelu"):
            self.assertIn(task, page)
        for price in ("59 euroa", "25 euroa", "89 euroa"):
            self.assertIn(price, page)

    def test_every_service_shows_its_student_price_and_the_condition(self):
        page = app.answer("/")[2].decode()
        for price, student in (("59 euroa", "53,10 euroa"), ("25 euroa", "22,50 euroa"),
                               ("89 euroa", "80,10 euroa"), ("49 euroa", "44,10 euroa")):
            self.assertIn(f'{price}<br><span class="student">Opiskelijoille {student}</span>', page)
        self.assertIn("Näytä opiskelijakortti korjaamolla.", page)

    def test_the_note_percent_comes_from_the_same_constant_as_the_prices(self):
        source = (pathlib.Path(content.__file__)).read_text(encoding="utf-8")
        self.assertNotIn("10 prosentin", source)
        self.assertIn(f"{content.STUDENT_PERCENT} prosentin", content.STUDENT_NOTE)

    def test_a_service_added_later_gets_a_student_price(self):
        original = content.SERVICES
        content.SERVICES = original + [("Uusi", "x", "100 euroa")]
        try:
            page = app.home()
        finally:
            content.SERVICES = original
        self.assertIn("Opiskelijoille 90,00 euroa", page)

    def test_the_chain_service_is_listed_after_tire_change_in_page_and_build(self):
        page = app.answer("/")[2].decode()
        self.assertIn("Ketjun vaihto", page)
        self.assertIn("Uusi ketju ja säätö.", page)
        self.assertIn('35 euroa<br><span class="student">Opiskelijoille 31,50 euroa</span>', page)
        self.assertLess(page.index("Renkaan vaihto"), page.index("Ketjun vaihto"))
        self.assertLess(page.index("Ketjun vaihto"), page.index("Sähköpyörän huolto"))
        with tempfile.TemporaryDirectory() as target:
            app.build(pathlib.Path(target))
            built = pathlib.Path(target, "index.html").read_text(encoding="utf-8")
        self.assertIn("Ketjun vaihto", built)
        self.assertIn("35 euroa", built)

    def test_the_phone_number_can_be_called_from_the_page(self):
        page = app.answer("/")[2].decode()
        self.assertIn('href="tel:+358501112222"', page)
        self.assertIn(">+358 50 111 2222</a>", page)
        self.assertNotIn("+358 40 123 4567", page)
        self.assertNotIn("358401234567", page)

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
        self.assertIn("Etsimääsi sivua ei löytynyt. Palaa etusivulle.", body.decode())

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


class VerifyWaits(unittest.TestCase):
    def test_an_earlier_page_or_a_missing_one_is_asked_for_again_until_the_commit_is_served(self):
        answers = iter([["answered 404"], ["is not commit abc's page"], []])
        asked = []
        real = verify.problems_of, verify.ASK_EVERY_SECONDS
        verify.problems_of = lambda url, commit: asked.append(url) or next(answers)
        verify.ASK_EVERY_SECONDS = 0
        try:
            self.assertEqual(verify.main("https://example.invalid/testaaja/", "abc"), 0)
        finally:
            verify.problems_of, verify.ASK_EVERY_SECONDS = real
        self.assertEqual(len(asked), 3)

    def test_a_site_that_does_not_answer_is_a_problem_not_a_crash(self):
        problems = verify.problems_of("http://127.0.0.1:1/?v=abc", "abc")
        self.assertEqual(len(problems), 1)
        self.assertIn("did not answer", problems[0])


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
            self.assertEqual(verify.main(base, "not-" + app.version(), wait_seconds=0), 1)
        finally:
            running.shutdown()
            running.server_close()
            thread.join()


if __name__ == "__main__":
    unittest.main()
