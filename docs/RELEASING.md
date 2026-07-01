# Releasing cool_maps to PyPI

Plain-language checklist for publishing a new version of `cool_maps` to **PyPI**
(the store that `pip` and `uv` install from). Follow it top to bottom.

> Background: for a long time PyPI only had the ancient `0.0.3` release, which
> pinned `cartopy<0.20` and failed to build on modern Python. Newer versions
> lived only on conda-forge. Publishing here keeps PyPI current so `pip`/`uv`
> users get a working package. See the history at the bottom.

---

## 0. One-time setup (do once per computer)

1. **PyPI account + access.** Have a PyPI account that is a *maintainer* of the
   `cool-maps` project (ask an existing owner to add you).
2. **API token.** On PyPI: *Account settings → API tokens → Add API token*.
   Copy the token (starts with `pypi-...`). Treat it like a password.
3. **Tools.** Install the build/upload tools:
   ```
   python3 -m pip install --upgrade build twine "packaging>=24.2"
   ```
   (`packaging>=24.2` matters — older versions make `twine check` falsely
   reject the modern metadata.)

**Never paste your token into the Claude Code `!` box** — it gets saved in the
chat. Use a real Terminal, or the `~/.pypirc` file described in step 6.

---

## 1. Make your code changes and commit them

Edit code as normal, then commit **everything** — the working tree must be
clean before building (see why in step 3):
```
git status          # should show nothing uncommitted when you're done
git add -A
git commit -m "Your change description"
```

## 2. Pick a NEW version number

Versions are `MAJOR.MINOR.PATCH` (e.g. `1.0.2`):
- **PATCH** (`1.0.1 → 1.0.2`): bug fix / packaging fix, no new features.
- **MINOR** (`1.0.2 → 1.1.0`): new features, nothing broken.
- **MAJOR** (`1.1.0 → 2.0.0`): breaking changes.

You **cannot reuse** a version number that already exists on PyPI **or**
conda-forge. Check existing versions:
```
git tag                 # versions released from this repo
```

## 3. Tag the version

This repo has **no version file to edit** — the version is read automatically
from the git tag by a tool called *versioneer*. So you just create a tag:
```
git tag 1.0.2           # use your chosen number
git describe --tags     # should print exactly "1.0.2" with no extra suffix
```

> Why the tree must be clean: if there are uncommitted changes or the tag isn't
> exactly on the current commit, versioneer produces something like
> `1.0.2+3.gabc1234.dirty`. **PyPI rejects any version with a `+...` suffix.**
> A clean tree + tag on the current commit gives a plain `1.0.2`.

## 4. Build the package

```
rm -rf dist/ build/ *.egg-info      # clear old builds
python3 -m build
```
This creates two files in `dist/`:
- `cool_maps-1.0.2.tar.gz` — the raw-source bundle (*sdist*)
- `cool_maps-1.0.2-py2.py3-none-any.whl` — the ready-made bundle (*wheel*)

> If the build fails with a missing file like `HISTORY.rst`, it means
> `MANIFEST.in` is missing a file that `setup.py` reads at build time. Add the
> file to `MANIFEST.in`, commit, and rebuild. (This was fixed in 1.0.2.)

## 5. Check the build

```
python3 -m twine check dist/*
```
Both files must say **PASSED**. If you see an error about a `license-file`
field, your `packaging` library is too old — run
`python3 -m pip install --upgrade "packaging>=24.2"` and check again.

## 6. Upload to PyPI

Run this **in a real Terminal window** (Terminal.app), NOT the Claude `!` box —
the upload asks for your token in a hidden prompt that only a real terminal
supports:
```
python3 -m twine upload dist/*
```
- **username:** `__token__`  (literally that word)
- **password:** paste your `pypi-...` token (the field stays blank as you
  paste — that's normal)

**Optional — skip the prompt forever.** Create a file at `~/.pypirc`:
```ini
[pypi]
  username = __token__
  password = pypi-XXXXXXXXXXXX
```
Then `python3 -m twine upload dist/*` uploads with no prompt (works anywhere).
Keep this file private (`chmod 600 ~/.pypirc`).

## 7. Push the tag to GitHub

So GitHub and PyPI agree on what `1.0.2` is:
```
git push origin main
git push origin 1.0.2
```

## 8. Verify it worked

- Visit https://pypi.org/project/cool-maps/ — the new version should be listed.
- Test install in a throwaway environment:
  ```
  pip install --upgrade cool-maps
  python -c "import cool_maps; print(cool_maps.__version__)"
  ```

---

## Quick reference (the whole thing, once set up)

```
git add -A && git commit -m "..."      # 1. commit changes
git tag 1.0.2                          # 2-3. new version tag
git describe --tags                    #      confirm clean "1.0.2"
rm -rf dist/ build/ *.egg-info         # 4. build
python3 -m build
python3 -m twine check dist/*          # 5. must say PASSED
python3 -m twine upload dist/*         # 6. upload (real Terminal)
git push origin main && git push origin 1.0.2   # 7. push tag
```

---

## Common problems

| Symptom | Cause | Fix |
|---|---|---|
| Version has `+...` or `.dirty` | Uncommitted changes / tag not on current commit | Commit everything, re-tag, rebuild |
| `FileNotFoundError` during build (e.g. `HISTORY.rst`) | `MANIFEST.in` missing a file `setup.py` reads | Add file to `MANIFEST.in`, commit, rebuild |
| `twine check` errors on `license-file` | `packaging` library too old | `pip install --upgrade "packaging>=24.2"` |
| Upload ends in `EOFError` / `termios.error` | Ran the upload in a non-interactive shell (e.g. Claude `!` box) | Run in a real Terminal, or use `~/.pypirc` |
| `File already exists` from PyPI | That version number was already published | Pick a new version number; you cannot overwrite |

---

## History / why this doc exists

- `cartopy<0.20` was pinned in early releases; removed in Sep 2022 (commit
  `bd1b95a`). Modern releases use unpinned cartopy.
- PyPI had only `0.0.3` (broken on modern Python) until `1.0.2`. Newer versions
  had only been published to conda-forge (`conda install -c conda-forge cool_maps`).
- `1.0.2` also fixed `MANIFEST.in` so the source bundle is self-contained.
