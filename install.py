#!/usr/bin/env python3
"""Preview or install only the bundled MicNow Lab skill (Python 3.9+)."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import stat
import tempfile
import uuid


SKILL_NAME = "micnow-lab"
SOURCE = Path(__file__).absolute().parent / "skills" / SKILL_NAME
AGENT_FOLDERS = {"codex": ".agents", "cursor": ".agents", "gemini": ".agents",
                 "qwen-code": ".agents", "kimi-cli": ".agents",
                 "claude-code": ".claude", "workbuddy": ".codebuddy",
                 "deepseek-harness": ".dsh"}
RESOURCE_DIRS = {"agents", "assets", "references", "scripts"}
SUFFIXES = {".md", ".py", ".yaml", ".yml", ".html", ".css", ".js", ".svg",
            ".png", ".jpg", ".jpeg", ".webp", ".woff2", ".txt"}
REQUIRED = {"SKILL.md", "scripts/serve_device_lab.py", "scripts/device_client.py",
            "scripts/device_bridge.py", "scripts/device_sim.py"}


class InstallError(ValueError):
    pass


def checked_path(value):
    """Reject traversal and symlinks, including symlinked parent directories."""
    path = Path(value).expanduser()
    if ".." in path.parts:
        raise InstallError("Parent traversal (..) is not accepted; use an explicit path.")
    path = path.absolute()
    for part in reversed((path, *path.parents)):
        try:
            info = part.lstat()
        except FileNotFoundError:
            continue
        if stat.S_ISLNK(info.st_mode):
            raise InstallError("Symlink paths are not accepted: " + str(part))
        if part != path and not stat.S_ISDIR(info.st_mode):
            raise InstallError("A parent path is not a directory: " + str(part))
    return path


def read_regular_file(path):
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(str(path), flags)
    with os.fdopen(descriptor, "rb") as stream:
        if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
            raise InstallError("Only regular resource files are supported: " + str(path))
        return stream.read()


def inventory(directory):
    """Read packaged resources, never credential files or arbitrary root files."""
    directory = checked_path(directory)
    if not directory.is_dir():
        raise InstallError("Skill path is not a directory: " + str(directory))
    result = {}

    def visit(folder, relative=Path()):
        with os.scandir(folder) as entries:
            for entry in sorted(entries, key=lambda item: item.name):
                item = relative / entry.name
                path = directory / item
                if entry.is_symlink():
                    raise InstallError("Symlink resources are not accepted: " + str(path))
                if entry.name in {"__pycache__", ".DS_Store"} or entry.name.endswith(".pyc"):
                    continue
                if entry.name.startswith("."):
                    raise InstallError("Unexpected hidden resource (not read): " + str(path))
                if entry.is_dir(follow_symlinks=False):
                    if len(item.parts) == 1 and entry.name not in RESOURCE_DIRS:
                        raise InstallError("Unexpected resource directory: " + str(path))
                    visit(path, item)
                elif entry.is_file(follow_symlinks=False):
                    if ((len(item.parts) == 1 and entry.name not in {"SKILL.md", "USAGE.md", "ASSET-SOURCES.md"})
                            or path.suffix.lower() not in SUFFIXES):
                        raise InstallError("Unexpected resource (not read): " + str(path))
                    result[item.as_posix()] = read_regular_file(path)
                else:
                    raise InstallError("Special files are not accepted: " + str(path))

    visit(directory)
    if not REQUIRED <= result.keys():
        raise InstallError("Skill is incomplete; missing: " + ", ".join(sorted(REQUIRED - result.keys())))
    return result


def resolve_destination(agent=None, project=None, scope=None, destination=None):
    """Return the skill parent directory; no directories are created here."""
    if destination is not None:
        if project is not None or scope is not None:
            raise InstallError("Use --destination by itself, without --project or --scope.")
        return checked_path(destination)
    if agent not in AGENT_FOLDERS:
        raise InstallError("Choose --agent or provide an explicit --destination skill parent directory.")
    if project is not None and scope == "user":
        raise InstallError("--project cannot be combined with --scope user.")
    scope = scope or ("project" if project is not None else "user")
    if scope == "project":
        if project is None:
            raise InstallError("Project installation requires an explicit --project path.")
        base = checked_path(project)
        if not base.is_dir():
            raise InstallError("The project must be an existing directory: " + str(base))
    elif scope == "user":
        if agent == "workbuddy":
            raise InstallError("WorkBuddy requires --project or an explicit --destination; no user path is assumed.")
        if agent == "deepseek-harness":
            # Official Harness override; project roots remain project/.dsh.
            dsh_home = os.environ.get("DSH_HOME")
            if dsh_home:
                return checked_path(Path(dsh_home) / "skills")
        base = checked_path(Path.home())
    else:
        raise InstallError("Scope must be user or project.")
    return checked_path(base / AGENT_FOLDERS[agent] / "skills")


def manifest_digest(files):
    manifest = {name: hashlib.sha256(data).hexdigest() for name, data in sorted(files.items())}
    return hashlib.sha256(json.dumps(manifest, sort_keys=True).encode("utf-8")).hexdigest()


def install(source, destination, apply=False, update=False):
    source = checked_path(source)
    parent = checked_path(destination)
    if parent == Path(parent.anchor) or parent.name == SKILL_NAME:
        raise InstallError("Destination must be a skill parent directory, not a filesystem root or micnow-lab itself.")
    target = checked_path(parent / SKILL_NAME)
    if target == source or target in source.parents or source in target.parents:
        raise InstallError("Installation source and destination must not overlap.")
    if parent.exists() and not parent.is_dir():
        raise InstallError("Destination parent is not a directory: " + str(parent))
    files = inventory(source)
    existing = inventory(target) if target.exists() else None
    result = {"destination": str(target), "files": len(files),
              "manifest_sha256": manifest_digest(files), "backup": None}
    if existing == files:
        return dict(result, status="already-installed", verified=True, changed=False)
    if not apply:
        return dict(result, status="preview", action="update" if existing is not None else "install",
                    requires_update_flag=existing is not None, verified=False, changed=False)
    if existing is not None and not update:
        raise InstallError("A different MicNow Lab skill exists. Review the preview, then use --install --update.")

    # Backups sit outside the skills directory, so they are not duplicate skills.
    backup_parent = checked_path(parent.parent / ".micnow-lab-backups")
    if existing is not None and backup_parent.exists() and not backup_parent.is_dir():
        raise InstallError("Backup location is not a directory: " + str(backup_parent))
    parent.mkdir(parents=True, exist_ok=True)
    checked_path(parent)
    staging = Path(tempfile.mkdtemp(prefix=".micnow-lab-install-", dir=str(parent)))
    backup = None
    installed = False
    try:
        for name, content in files.items():
            output = staging / name
            output.parent.mkdir(parents=True, exist_ok=True)
            with output.open("xb") as stream:
                stream.write(content)
        if inventory(staging) != files:
            raise InstallError("Staged files do not match the source; installation stopped.")
        checked_path(target)
        current = inventory(target) if target.exists() else None
        if current != existing:
            raise InstallError("Destination changed during preparation; retry after reviewing its current state.")
        if existing is not None:
            backup_parent.mkdir(parents=True, exist_ok=True)
            checked_path(backup_parent)
            stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
            backup = backup_parent / (SKILL_NAME + "-" + stamp + "-" + uuid.uuid4().hex)
            os.rename(target, backup)
        try:
            os.rename(staging, target)
            installed = True
            if inventory(target) != files:
                raise InstallError("Installed files do not match the source.")
        except BaseException:
            # Put the previous tree back before removing our failed staging tree.
            if installed:
                os.rename(target, staging)
            if backup is not None:
                os.rename(backup, target)
                backup = None
            raise
    finally:
        if staging.exists():
            shutil.rmtree(staging)
    result["backup"] = str(backup) if backup is not None else None
    return dict(result, status="updated" if existing is not None else "installed",
                verified=True, changed=True)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--agent", choices=sorted(AGENT_FOLDERS))
    parser.add_argument("--project", help="Existing project directory; implies project scope")
    parser.add_argument("--scope", choices=("user", "project"))
    parser.add_argument("--destination", help="Explicit skill parent directory for any compatible local agent")
    parser.add_argument("--install", action="store_true", help="Perform the previewed installation")
    parser.add_argument("--update", action="store_true", help="Allow a differing installation to be replaced with a backup")
    args = parser.parse_args(argv)
    try:
        destination = resolve_destination(args.agent, args.project, args.scope, args.destination)
        result = install(SOURCE, destination, apply=args.install, update=args.update)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (InstallError, OSError) as error:
        print(json.dumps({"status": "error", "message": str(error)}, ensure_ascii=False))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
