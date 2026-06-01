# shaxelib

Minimal template for publishing a Haxe library to haxelib through GitHub Releases.

## What is included

- `src/` for library source code
- `tests/` for lightweight test entry points
- `run/Main.hx` as the CLI entry point for `haxelib run`
- `haxelib.yml` as the editable source of package metadata
- `.github/scripts/generate_haxelib_json.py` to build `package/haxelib.json`
- `.github/workflows/publish-haxelib.yml` to publish on release

## Intended workflow

1. Rename the project and set the real package name in `haxelib.yml`.
2. Replace placeholder values such as `AUTHOR` and `LIBRARY_NAME`.
3. Add your library code under `src/`.
4. Update tests in `tests/` so they compile against the real library.
5. Create a GitHub Release with a semantic version tag such as `v0.1.0`.
6. The workflow generates `package/haxelib.json` and submits the package to haxelib.

## Required setup

Update `haxelib.yml`:

- `name`
- `contributors`
- `description` if the GitHub repository description is empty
- `license` if automatic SPDX to haxelib mapping is not enough
- `dependencies` when your library requires other haxelib packages

Set GitHub Actions secrets:

- `HAXELIB_PASSWORD` required
- `HAXELIB_USER` optional for explicit username-based submit

## Local usage

Run tests:

```bash
haxe tests.hxml
```

Run the CLI entry point locally:

```bash
haxe -cp . -cp src --main run.Main --interp
```

## Current placeholders to replace

- `tests.hxml` still contains `-L LIBRARY_NAME`
- `haxelib.yml` still contains `AUTHOR`
- `run/Main.hx`, `src/Main.hx`, and `tests/Tests.hx` are empty stubs

## Project layout

### `src/`

This directory contains the public library source that will be shipped to haxelib.

- Put reusable library code here.
- Keep package names aligned with the library name you plan to publish.
- Only files copied into `package/src` are included in the published package.
- The runnable entry point for `haxelib run` lives separately in `run/Main.hx`.

`src/Main.hx` is only a stub. Replace it with your real modules or remove it if you do not need a root source module under `src/`.

### `run/`

This directory contains the CLI entry point used by `haxelib run <libraryname>`.

- `run/Main.hx` must stay compatible with `main: "run.Main"` in `haxelib.yml`.
- Keep command-line bootstrap logic here instead of mixing it into the library source tree.

### `tests/`

This directory contains compile-time or runtime tests for the library.

- `tests.hxml` adds `tests/` to the class path.
- `Tests` is the default test entry point.
- The current template expects the library to be available through `-L LIBRARY_NAME`.

Before using the test template, replace `LIBRARY_NAME` in `tests.hxml` with the actual haxelib package name, or switch the test setup to direct source class paths if that fits your workflow better.

Suggested usage:

- smoke tests that compile the public API
- regression tests for fixed bugs
- small interpreter-based checks with `--interp`

`tests/Tests.hx` is intentionally empty and should be replaced with real assertions or compile checks.

## Publish behavior

The release workflow:

1. Checks out the published Git tag
2. Installs Haxe and Python dependencies
3. Copies `src/`, `run/`, `README.md`, `LICENSE`, and optional `CHANGELOG.md` into `package/`
4. Generates `package/haxelib.json` from `haxelib.yml`, repository metadata, and the release body
5. Publishes `package/` with `haxelib submit`

## Notes

- Release notes must not be empty, because they become `releasenote` in `haxelib.json`.
- Repository topics are used as package tags when `tags` are not set in `haxelib.yml`.
- The generated package version comes from the Git tag unless `version` is set manually.
- `main: "run.Main"` is the package entry point used for `haxelib run <libraryname>`.
