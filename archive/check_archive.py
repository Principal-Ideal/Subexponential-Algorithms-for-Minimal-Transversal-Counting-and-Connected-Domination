"""Validate archive structure, local Markdown links and primary-proof dependencies.

Standard library only. This checks organization, not mathematical correctness.
The manifest grammar is deliberately small: quoted scalar strings, bare status
and method names, and inline JSON arrays. No content digests are produced.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import re
from urllib.parse import unquote, urlsplit


ARCHIVE = Path(__file__).resolve().parent
REPOSITORY = ARCHIVE.parent
STATUSES = {"imported", "established", "conditional"}
METHODS = {"hand", "exact-enum", "solver-z3", "solver-dual", "hybrid", "external"}
ID_RE = re.compile(r"[0-9]{3,}")
LINK_RE = re.compile(r"(?<!!)\[[^\]\n]*\]\(([^)\n]+)\)")


def parse_value(value: str):
    value = value.strip()
    if value.startswith(('"', '[')):
        return json.loads(value)
    if value.startswith("'") and value.endswith("'"):
        return value[1:-1].replace("''", "'")
    if value and re.fullmatch(r"[A-Za-z][A-Za-z0-9_-]*", value):
        return value
    raise ValueError(f"unsupported scalar or array: {value!r}")


def read_manifest(path: Path) -> dict:
    data: dict = {}
    section = None
    for number, line in enumerate(path.read_text(encoding="utf-8-sig").splitlines(), 1):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        match = re.fullmatch(r"(  )?([a-z_]+):\s*(.*)", line)
        if not match:
            raise ValueError(f"line {number}: unsupported YAML shape")
        indent, key, raw = match.groups()
        if indent:
            if section is None:
                raise ValueError(f"line {number}: indented field without a section")
            target = data[section]
        else:
            section = None
            target = data
        if key in target:
            raise ValueError(f"line {number}: duplicate key {key}")
        if not raw:
            if indent:
                raise ValueError(f"line {number}: nested sections are unsupported")
            target[key] = {}
            section = key
        else:
            target[key] = parse_value(raw)
    return data


def validate(through: str | None) -> dict:
    errors: list[str] = []
    warnings: list[str] = []
    manifests: dict[str, dict] = {}
    all_ids = sorted(p.name for p in ARCHIVE.iterdir() if p.is_dir() and ID_RE.fullmatch(p.name))
    selected_ids = [rid for rid in all_ids if through is None or int(rid) <= int(through)]
    excluded_ids = [rid for rid in all_ids if rid not in selected_ids]
    for rid in selected_ids:
        directory = ARCHIVE / rid
        for name in ("index.yaml", "artifacts.md"):
            if not (directory / name).is_file():
                errors.append(f"{rid}: missing required file {name}")
        manifest = directory / "index.yaml"
        if not manifest.is_file():
            continue
        try:
            record = read_manifest(manifest)
        except (ValueError, json.JSONDecodeError) as exc:
            errors.append(f"{rid}/index.yaml: {exc}")
            continue
        manifests[rid] = record
        if record.get("id") != rid:
            errors.append(f"{rid}: quoted id must equal directory name")
        if record.get("status") not in STATUSES:
            errors.append(f"{rid}: invalid or missing status")
        if not isinstance(record.get("result"), str) or not record["result"].strip():
            errors.append(f"{rid}: nonempty English result paragraph is required")
        proof = record.get("primary_proof")
        if not isinstance(proof, dict):
            errors.append(f"{rid}: primary_proof must be an object")
            continue
        if proof.get("method") not in METHODS:
            errors.append(f"{rid}: invalid or missing primary proof method")
        for field in ("requires", "motivated_by"):
            refs = proof.get(field)
            if not isinstance(refs, list) or any(not isinstance(v, str) or not ID_RE.fullmatch(v) for v in refs):
                errors.append(f"{rid}: {field} must be an array of quoted numeric IDs")
                continue
            if len(set(refs)) != len(refs):
                errors.append(f"{rid}: duplicate {field} entry")
            for ref in refs:
                if ref not in all_ids or not (ARCHIVE / ref / "index.yaml").is_file():
                    errors.append(f"{rid}: nonexistent {field} reference {ref}")
            if field == "requires" and rid in refs:
                errors.append(f"{rid}: self prerequisite")
        if record.get("status") == "imported" and proof.get("method") != "external":
            warnings.append(f"{rid}: imported result does not use external method; inspect intent")
        if proof.get("method") == "external" and record.get("status") != "imported":
            warnings.append(f"{rid}: external method has a non-imported status; inspect intent")

    visiting: set[str] = set()
    visited: set[str] = set()
    order: list[str] = []

    def visit(rid: str, trail: list[str]):
        if rid in visiting:
            errors.append("requires cycle: " + " -> ".join(trail + [rid]))
            return
        if rid in visited or rid not in manifests:
            return
        visiting.add(rid)
        refs = manifests[rid].get("primary_proof", {}).get("requires", [])
        if isinstance(refs, list):
            for ref in refs:
                if isinstance(ref, str):
                    visit(ref, trail + [rid])
        visiting.remove(rid)
        visited.add(rid)
        order.append(rid)

    for rid in selected_ids:
        visit(rid, [])

    local_links = 0
    external_links = 0
    checked_markdown = 0
    for path in sorted(REPOSITORY.rglob("*.md")):
        relative = path.relative_to(REPOSITORY)
        if any(part in {".git", "workspace", ".venv", "venv", "__pycache__"}
               for part in relative.parts):
            continue
        if (len(relative.parts) > 1 and relative.parts[0] == "archive"
                and relative.parts[1] in excluded_ids):
            continue
        checked_markdown += 1
        source = path.read_text(encoding="utf-8-sig")
        for match in LINK_RE.finditer(source):
            link = match.group(1).strip()
            if link.startswith("<") and link.endswith(">"):
                link = link[1:-1]
            # Markdown optional title is outside the path. Current manifests
            # use no such titles, but permit the conventional quoted suffix.
            link = re.sub(r'\s+"[^\"]*"$', '', link)
            if link.startswith("#"):
                continue  # Heading anchors are intentionally not validated.
            parsed = urlsplit(link)
            if parsed.scheme or parsed.netloc:
                external_links += 1
                continue
            local_links += 1
            target = (path.parent / unquote(parsed.path)).resolve()
            try:
                target.relative_to(REPOSITORY)
            except ValueError:
                errors.append(f"{relative}: local link leaves repository: {link}")
                continue
            if not target.exists():
                errors.append(f"{relative}: missing local link target: {link}")

    required_edges = sum(len(r.get("primary_proof", {}).get("requires", []))
                         for r in manifests.values()
                         if isinstance(r.get("primary_proof", {}).get("requires", []), list))
    return {
        "status": "passed" if not errors else "failed",
        "checked_at_utc": datetime.now(timezone.utc).isoformat(),
        "scope": "Archive structure and local references only; not mathematical, external-URL, solver, or formal verification",
        "through": through,
        "result_count": len(manifests),
        "selected_ids": selected_ids,
        "excluded_ids": excluded_ids,
        "required_edges": required_edges,
        "topological_order_prerequisites_first": order,
        "markdown_files_checked": checked_markdown,
        "local_link_targets_checked": local_links,
        "external_links_recorded_not_fetched": external_links,
        "warnings": warnings,
        "errors": errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--through", help="Validate result IDs no greater than this numeric ID")
    parser.add_argument("--output", type=Path, default=REPOSITORY / "workspace" / "archive_check.json")
    args = parser.parse_args()
    if args.through is not None and not ID_RE.fullmatch(args.through):
        parser.error("--through must be a quoted-style numeric ID with at least three digits")
    report = validate(args.through)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    text_path = args.output.with_suffix(".txt")
    summary = [f"Archive check: {report['status']}",
               f"Results: {report['result_count']}; prerequisite edges: {report['required_edges']}",
               f"Markdown files: {report['markdown_files_checked']}; local links: {report['local_link_targets_checked']}",
               report['scope']]
    summary.extend("ERROR: " + message for message in report["errors"])
    summary.extend("WARNING: " + message for message in report["warnings"])
    text_path.write_text("\n".join(summary) + "\n", encoding="utf-8")
    print("\n".join(summary))
    return int(bool(report["errors"]))


if __name__ == "__main__":
    raise SystemExit(main())
