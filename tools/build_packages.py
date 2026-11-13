#!/usr/bin/env python3
"""Build and verify reproducible skill archives; performs no installation or upload."""
import hashlib
from pathlib import Path
import sys
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from install import inventory

VERSION = "0.5.0"


def main():
    files = inventory(ROOT / "skills" / "micnow-lab")
    output = ROOT / "downloads"
    output.mkdir(exist_ok=True)
    checksums = []
    for name, prefix in (("micnow-lab-" + VERSION, "micnow-lab/"),
                         ("micnow-lab-perplexity-" + VERSION, "")):
        archive = output / (name + ".zip")
        with ZipFile(archive, "w", compression=ZIP_DEFLATED) as stream:
            for path, content in sorted(files.items()):
                item = ZipInfo(prefix + path, date_time=(2026, 11, 13, 0, 0, 0))
                item.compress_type = ZIP_DEFLATED
                item.external_attr = 0o100644 << 16
                stream.writestr(item, content)
        with ZipFile(archive) as check:
            if check.testzip() or set(check.namelist()) != {prefix + path for path in files}:
                raise ValueError("Archive integrity mismatch")
            if any(check.read(prefix + path) != content for path, content in files.items()):
                raise ValueError("Archive differs from source")
            if len(check.namelist()) > 100 or archive.stat().st_size > 20 * 1024 * 1024:
                raise ValueError("Archive exceeds supported import limits")
        checksums.append(hashlib.sha256(archive.read_bytes()).hexdigest() + "  " + archive.name)
        print(archive.name + ": " + str(len(files)) + " files, " + str(archive.stat().st_size) + " bytes")
    (output / "SHA256SUMS.txt").write_text("\n".join(checksums) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
