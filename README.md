# Posse Demo Oy

The website of Posse Demo Oy, a bicycle repair shop in Helsinki: one Finnish page with the
services, prices, opening hours and contact details. The test client of Posse, TRIAC Anvil's
second installation.

| File | Holds |
| --- | --- |
| `content.py` | Every word a visitor reads |
| `app.py` | The page, served by Python's standard library; `--build <dir>` writes it as static files |
| `tests/` | The tests: each address, the static copy, a real server on a free port |
| `check.sh` | The whole check |
| `verify.py` | After a deploy: an environment's directory serves this commit's page |
| `.github/workflows/anvil-deploy.yml` | Deploys a candidate to one directory of the koesivusto (GitHub Pages: `testaaja/`, `toinen/`, `yla/`, kept on the branch `gh-pages`), with pictures at two widths |

Run it: `python3 app.py` prints a port; open `http://127.0.0.1:<port>/`. Check it: `./check.sh`
(Python 3.12 or later, nothing else).
