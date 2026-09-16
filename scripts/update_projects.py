#!/usr/bin/env python3
"""Refresh the static portfolio from curated data and public GitHub metadata."""

import argparse
from datetime import datetime, timezone
from html import escape
import json
import os
from pathlib import Path
import re
import sys
import tempfile
from urllib.error import URLError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parent.parent
OWNER = "tomeido"
START = "<!-- PROJECTS:START -->"
END = "<!-- PROJECTS:END -->"
CATEGORIES = {
    "computational": "Computational Design",
    "web": "Web Apps",
    "ai": "AI / ML",
    "tools": "Tools",
}
LANGUAGE_COLORS = {
    "C#": "#178600", "CSS": "#563d7c", "HTML": "#e34c26",
    "JavaScript": "#f1e05a", "Python": "#3572a5", "Rust": "#dea584",
    "TypeScript": "#3178c6", "Go": "#00add8", "Shell": "#89e051",
}


def load_json(path):
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def fetch_repositories():
    """Collect every page; any request failure prevents updating the page."""
    repositories = []
    page = 1
    while True:
        url = (
            f"https://api.github.com/users/{OWNER}/repos"
            f"?type=owner&sort=full_name&direction=asc&per_page=100&page={page}"
        )
        request = Request(url, headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": f"{OWNER}-portfolio-updater",
            "X-GitHub-Api-Version": "2022-11-28",
        })
        with urlopen(request, timeout=30) as response:
            batch = json.load(response)
        if not isinstance(batch, list):
            raise ValueError(f"GitHub page {page} did not contain a repository list")
        repositories.extend(batch)
        if len(batch) < 100:
            return repositories
        page += 1


def text_field(item, field, context):
    value = item.get(field)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{context}: {field} must be a nonempty string")
    return value.strip()


def validated_url(value, context):
    if not isinstance(value, str) or any(char.isspace() for char in value):
        raise ValueError(f"{context}: expected an HTTPS URL without whitespace")
    parsed = urlsplit(value)
    if (
        parsed.scheme != "https"
        or not parsed.hostname
        or parsed.username is not None
        or parsed.password is not None
    ):
        raise ValueError(f"{context}: expected an HTTPS URL without credentials")
    # Accessing port validates malformed or out-of-range explicit ports.
    parsed.port
    return value


def prepare_projects(curated, repositories):
    if not isinstance(curated, list) or not curated:
        raise ValueError("Project data must be a nonempty JSON array")
    if not isinstance(repositories, list) or not repositories:
        raise ValueError("Repository metadata must be a nonempty JSON array")

    by_name = {}
    for repo in repositories:
        if not isinstance(repo, dict):
            raise ValueError("Repository metadata contains a non-object entry")
        name = text_field(repo, "name", "Repository")
        key = name.casefold()
        if key in by_name:
            raise ValueError(f"Duplicate repository metadata: {name}")
        by_name[key] = repo

    projects = []
    seen = set()
    for entry in curated:
        if not isinstance(entry, dict):
            raise ValueError("Project data contains a non-object entry")
        if set(entry) - {"name", "category", "description", "demo"}:
            raise ValueError("Project data contains an unsupported field")
        name = text_field(entry, "name", "Project")
        if not re.fullmatch(r"[A-Za-z0-9_.-]+", name):
            raise ValueError(f"Invalid repository name: {name}")
        key = name.casefold()
        if key in seen:
            raise ValueError(f"Duplicate curated project: {name}")
        seen.add(key)
        category = text_field(entry, "category", name)
        if category not in CATEGORIES:
            raise ValueError(f"{name}: unknown category {category}")
        description = text_field(entry, "description", name)
        demo = validated_url(entry["demo"], f"{name} demo") if "demo" in entry else None

        repo = by_name.get(key)
        if repo is None:
            raise ValueError(f"Missing public repository metadata: {name}")
        if repo.get("private") is not False or repo.get("fork") is not False:
            raise ValueError(f"{name}: curated repositories must be public and not forks")
        owner = repo.get("owner")
        if not isinstance(owner, dict) or owner.get("login") != OWNER:
            raise ValueError(f"{name}: repository must belong to {OWNER}")
        repo_name = text_field(repo, "name", name)
        url = text_field(repo, "html_url", name)
        if url != f"https://github.com/{OWNER}/{repo_name}":
            raise ValueError(f"{name}: unexpected GitHub repository URL")
        pushed_at = text_field(repo, "pushed_at", name)
        try:
            pushed = datetime.fromisoformat(pushed_at.replace("Z", "+00:00"))
        except ValueError as error:
            raise ValueError(f"{name}: invalid pushed_at timestamp") from error
        if pushed.tzinfo is None:
            raise ValueError(f"{name}: pushed_at must include a timezone")
        pushed = pushed.astimezone(timezone.utc)
        if "language" not in repo:
            raise ValueError(f"{name}: missing language metadata")
        language = repo["language"]
        if language is not None and (not isinstance(language, str) or not language.strip()):
            raise ValueError(f"{name}: language must be a string or null")
        projects.append({
            "name": repo_name, "category": category, "description": description,
            "demo": demo, "url": url, "language": language or "기타", "pushed": pushed,
        })

    projects.sort(key=lambda project: (-project["pushed"].timestamp(), project["name"].casefold()))
    return projects


def render_card(project):
    name = escape(project["name"])
    category = escape(project["category"])
    label = escape(CATEGORIES[project["category"]])
    language = escape(project["language"])
    color = LANGUAGE_COLORS.get(project["language"], "#8b949e")
    pushed = project["pushed"]
    timestamp = pushed.isoformat(timespec="seconds").replace("+00:00", "Z")
    date = pushed.strftime("%Y-%m-%d")
    date_label = pushed.strftime("%Y.%m.%d")
    demo = ""
    if project["demo"]:
        demo = (
            f'\n          <a class="demo-link" href="{escape(project["demo"])}" '
            'target="_blank" rel="noopener noreferrer">사이트 열기 '
            '<span aria-hidden="true">↗</span></a>'
        )
    return f'''      <article class="card" data-cat="{category}" data-lang="{language}" data-name="{name}" data-updated="{timestamp}">
        <div class="card-header">
          <h3 class="card-title"><a href="{escape(project["url"])}" target="_blank" rel="noopener noreferrer">{name} <span aria-hidden="true">↗</span></a></h3>
        </div>
        <p class="card-desc">{escape(project["description"])}</p>
        <div class="card-footer">
          <span class="lang-badge"><span class="lang-dot" style="background:{color}" aria-hidden="true"></span>{language}</span>
          <span class="cat-badge">{label}</span>
        </div>
        <div class="card-actions">
          <time datetime="{date}">최근 변경 {date_label}</time>{demo}
        </div>
      </article>'''


def render_page(html, projects):
    if html.count(START) != 1 or html.count(END) != 1:
        raise ValueError("HTML must have exactly one pair of PROJECTS markers")
    before, remainder = html.split(START)
    if END not in remainder:
        raise ValueError("PROJECTS markers are in the wrong order")
    _, after = remainder.split(END)
    cards = "\n\n".join(render_card(project) for project in projects)
    result = f"{before}{START}\n{cards}\n      {END}{after}"
    date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    date_label = date.replace("-", ".")
    pattern = r'<time\b(?=[^>]*\bid=[\"\']updated-date[\"\'])[^>]*>[^<]*</time>'
    result, replacements = re.subn(
        pattern,
        f'<time id="updated-date" datetime="{date}">{date_label}</time>',
        result,
    )
    if replacements != 1:
        raise ValueError("HTML must have exactly one updated-date time element")
    return result


def write_atomic(path, content):
    """Keep the current file intact until all data and HTML have been validated."""
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=path.parent, prefix=f".{path.name}.", delete=False
        ) as handle:
            temporary = Path(handle.name)
            handle.write(content)
        temporary.chmod(path.stat().st_mode & 0o777)
        os.replace(temporary, path)
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot", type=Path, help="Read a complete public repository JSON array offline")
    parser.add_argument("--index", type=Path, default=ROOT / "index.html", help="HTML page to update")
    parser.add_argument("--data", type=Path, default=ROOT / "data" / "projects.json", help="Curated project JSON")
    args = parser.parse_args()
    try:
        curated = load_json(args.data)
        repositories = load_json(args.snapshot) if args.snapshot else fetch_repositories()
        projects = prepare_projects(curated, repositories)
        existing = args.index.read_text(encoding="utf-8")
        rendered = render_page(existing, projects)
        if rendered != existing:
            write_atomic(args.index, rendered)
        print(f"Updated {args.index} from public metadata for {len(projects)} curated projects.")
        return 0
    except (OSError, ValueError, URLError) as error:
        print(f"Update aborted; HTML was not changed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
