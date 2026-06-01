import os
import re
import sys
import json
import yaml
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = ROOT / "haxelib.yml"
OUT_PATH = ROOT / "package" / "haxelib.json"


HAXELIB_LICENSE_MAP = {
    "MIT": "MIT",
    "Apache-2.0": "Apache",
    "BSD-2-Clause": "BSD",
    "BSD-3-Clause": "BSD",
    "GPL-2.0": "GPL",
    "GPL-3.0": "GPL",
    "LGPL-2.1": "LGPL",
    "LGPL-3.0": "LGPL",
    "MPL-2.0": "MPL",
    "Unlicense": "Public",
    "CC0-1.0": "Public",
}


def fail(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    sys.exit(1)


def read_json_file(path: str | Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_yaml() -> dict:
    if not CONFIG_PATH.exists():
        fail("haxelib.yml not found")

    with CONFIG_PATH.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    if not isinstance(data, dict):
        fail("haxelib.yml must contain a YAML object")

    return data


def github_api_get(path: str) -> dict:
    token = os.environ.get("GITHUB_TOKEN")
    repo = os.environ.get("GITHUB_REPOSITORY")

    if not token:
        fail("GITHUB_TOKEN is missing")
    if not repo:
        fail("GITHUB_REPOSITORY is missing")

    request = urllib.request.Request(
        f"https://api.github.com/repos/{repo}{path}",
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )

    with urllib.request.urlopen(request) as response:
        return json.loads(response.read().decode("utf-8"))


def get_release_payload() -> dict:
    event_path = os.environ.get("GITHUB_EVENT_PATH")
    if not event_path:
        fail("GITHUB_EVENT_PATH is missing")

    event = read_json_file(event_path)
    release = event.get("release")

    if not isinstance(release, dict):
        fail("This workflow must be triggered by a GitHub Release event")

    return release


def normalize_version(tag_name: str) -> str:
    version = tag_name.strip()

    if version.startswith("v"):
        version = version[1:]

    if not re.match(r"^\d+\.\d+\.\d+([.-][A-Za-z0-9.-]+)?$", version):
        fail(
            f"Invalid version from release tag: {tag_name!r}. "
            "Use tags like v0.1.0, v1.2.3, v1.0.0-beta.1."
        )

    return version


def normalize_name(name: str) -> str:
    name = str(name).strip()

    if not name:
        fail("Package name is empty")

    if not re.match(r"^[A-Za-z0-9_.-]+$", name):
        fail(
            f"Invalid package name: {name!r}. "
            "Use only letters, numbers, underscore, dot or hyphen."
        )

    return name


def normalize_tags(tags) -> list[str]:
    if tags is None:
        return []

    if not isinstance(tags, list):
        fail("tags must be a YAML array or GitHub topics array")

    result = []
    for tag in tags:
        value = str(tag).strip()
        if value:
            result.append(value)

    return result


def normalize_dependencies(dependencies) -> dict:
    if dependencies is None:
        return {}

    if not isinstance(dependencies, dict):
        fail("dependencies must be a YAML object")

    return {
        str(name): "" if version is None else str(version)
        for name, version in dependencies.items()
    }


def main() -> None:
    config = load_yaml()
    release = get_release_payload()

    repo_data = github_api_get("")
    topics_data = github_api_get("/topics")

    repo_name = repo_data.get("name") or ""
    repo_url = repo_data.get("html_url") or ""
    repo_description = repo_data.get("description") or ""
    repo_topics = topics_data.get("names") or []

    release_tag = release.get("tag_name") or ""
    release_body = release.get("body") or ""

    license_info = repo_data.get("license") or {}
    spdx_license = license_info.get("spdx_id")

    haxelib_license = config.get("license")
    if not haxelib_license:
        haxelib_license = HAXELIB_LICENSE_MAP.get(spdx_license)

    if not haxelib_license:
        fail(
            f"Cannot map GitHub license {spdx_license!r} to haxelib license. "
            "Set license explicitly in haxelib.yml."
        )

    if not release_body.strip():
        fail("GitHub Release body is empty. Fill release notes before publishing.")

    package = {
        "name": normalize_name(config.get("name") or repo_name),
        "url": str(config.get("url") or repo_url),
        "license": str(haxelib_license),
        "tags": normalize_tags(config.get("tags", repo_topics)),
        "description": str(config.get("description") or repo_description),
        "version": str(config.get("version") or normalize_version(release_tag)),
        "classPath": str(config.get("classPath", "src")),
        "releasenote": str(config.get("releasenote") or release_body.strip()),
        "contributors": config.get("contributors") or [],
    }

    if not package["description"]:
        fail("Description is empty. Add GitHub repo description or description in haxelib.yml.")

    if not package["contributors"]:
        fail("contributors is required. Add contributors to haxelib.yml.")

    dependencies = normalize_dependencies(config.get("dependencies"))
    if dependencies:
        package["dependencies"] = dependencies

    if "main" in config and config["main"]:
        package["main"] = str(config["main"])

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    with OUT_PATH.open("w", encoding="utf-8") as f:
        json.dump(package, f, indent=2, ensure_ascii=False)
        f.write("\n")

    print(f"Generated {OUT_PATH}")
    print(json.dumps(package, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
