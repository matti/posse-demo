# Working rules for this repository

- Python's standard library only. No package is installed, by the check or by the site.
- Every word a visitor reads is Finnish and lives in `content.py`, nowhere else.
- `./check.sh` is the whole check. It runs without a network. Run it before you finish.
- A change a visitor can see has a test in `tests/` that asserts on what the page then says.
- Tests wait for an event (a server that listens, a page that answers), never for an amount of
  time, and bind port 0, never a fixed port.
- `.github/workflows/anvil-deploy.yml` deploys and verifies; change it only with a person's grant.
