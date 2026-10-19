#!/usr/bin/env python3
"""Restore the archived M4A audit workspace without touching the application."""

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import shutil
import tarfile
import tempfile


ROOT_NAME = "m4a-alternatives"


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def safe_relative(value):
    if not isinstance(value, str) or not value or "\\" in value or ":" in value:
        raise ValueError(f"Invalid relative path: {value!r}")
    path = PurePosixPath(value)
    if path.is_absolute() or any(p in ("", ".", "..") for p in value.split("/")):
        raise ValueError(f"Unsafe relative path: {value!r}")
    return path


def load_manifest(snapshot):
    manifest = json.loads((snapshot / "manifest.json").read_text(encoding="utf-8"))
    if manifest["schema_version"] != 1 or manifest["root_directory"] != ROOT_NAME:
        raise ValueError("Unsupported checkpoint manifest")
    files = {}
    for entry in manifest["files"]:
        name = str(safe_relative(entry["path"]))
        if name in files:
            raise ValueError(f"Duplicate manifest entry: {name}")
        if not isinstance(entry["bytes"], int) or entry["bytes"] < 0:
            raise ValueError(f"Invalid size: {name}")
        checksum = entry["sha256"]
        if len(checksum) != 64 or any(c not in "0123456789abcdef" for c in checksum):
            raise ValueError(f"Invalid SHA-256: {name}")
        files[name] = entry
    if len(files) != manifest["file_count"]:
        raise ValueError("Manifest file count mismatch")
    if sum(e["bytes"] for e in files.values()) != manifest["uncompressed_bytes"]:
        raise ValueError("Manifest byte count mismatch")
    return manifest, files


def verify(root, files):
    if root.is_symlink() or not root.is_dir():
        raise ValueError(f"Missing directory or symlink: {root}")
    for name, entry in files.items():
        path = root / name
        current = path
        while current != root:
            if current.is_symlink():
                raise ValueError(f"Symlink in checkpoint path: {current}")
            current = current.parent
        if not path.is_file() or path.stat().st_size != entry["bytes"]:
            raise ValueError(f"Missing file or incorrect size: {path}")
        if digest(path) != entry["sha256"]:
            raise ValueError(f"SHA-256 mismatch: {path}")


def restore(snapshot, destination, manifest, files):
    archive_name = str(safe_relative(manifest["archive"]["file"]))
    if "/" in archive_name:
        raise ValueError("Archive must be adjacent to manifest")
    archive = snapshot / archive_name
    if archive.stat().st_size != manifest["archive"]["bytes"]:
        raise ValueError("Archive size mismatch")
    if digest(archive) != manifest["archive"]["sha256"]:
        raise ValueError("Archive SHA-256 mismatch")
    destination.mkdir(parents=True, exist_ok=True)
    target = destination / ROOT_NAME
    if target.exists() or target.is_symlink():
        raise ValueError(f"Refusing to overwrite {target}; use --verify-only or another destination")
    with tempfile.TemporaryDirectory(prefix=".m4a-restore-", dir=destination) as temporary:
        temporary = Path(temporary)
        root = temporary / ROOT_NAME
        seen = set()
        with tarfile.open(archive, "r:xz") as bundle:
            for member in bundle:
                path = safe_relative(member.name)
                if len(path.parts) < 2 or path.parts[0] != ROOT_NAME or not member.isfile():
                    raise ValueError(f"Unexpected archive entry: {member.name}")
                relative = str(PurePosixPath(*path.parts[1:]))
                if relative not in files or relative in seen:
                    raise ValueError(f"Unknown or duplicate archive file: {relative}")
                if member.size != files[relative]["bytes"] or getattr(member, "sparse", None):
                    raise ValueError(f"Invalid archive size/type: {relative}")
                output = root / relative
                output.parent.mkdir(parents=True, exist_ok=True)
                with bundle.extractfile(member) as source, output.open("xb") as stream:
                    shutil.copyfileobj(source, stream)
                output.chmod(0o644)
                seen.add(relative)
        if seen != set(files):
            raise ValueError("Incomplete archive")
        verify(root, files)
        # Recheck before publication; all extraction took place in a private directory.
        if target.exists() or target.is_symlink():
            raise ValueError(f"Destination appeared during restore: {target}")
        root.rename(target)
    return target


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--destination", type=Path, required=True,
                        help="Parent of the restored m4a-alternatives directory")
    parser.add_argument("--snapshot-dir", type=Path,
                        default=Path(__file__).resolve().parents[3] /
                        "docs/m4a/alternatives/checkpoint")
    parser.add_argument("--verify-only", action="store_true",
                        help="Check saved files in an existing workspace, without writing")
    args = parser.parse_args()
    manifest, files = load_manifest(args.snapshot_dir)
    if args.verify_only:
        target = args.destination / ROOT_NAME
        verify(target, files)
    else:
        target = restore(args.snapshot_dir, args.destination, manifest, files)
    print(json.dumps({"operation": "verify" if args.verify_only else "restore",
                      "directory": str(target), "verified_files": len(files),
                      "verified_bytes": manifest["uncompressed_bytes"]}, indent=2))


if __name__ == "__main__":
    main()
