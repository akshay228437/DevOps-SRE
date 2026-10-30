"""Update the three deployment images and version labels using only stdlib."""

import argparse
from pathlib import Path
import re


def update_images(root, repository, sha):
    if not re.fullmatch(r"[0-9a-f]{40}", sha):
        raise ValueError("Expected a full 40-character lowercase commit SHA")
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository):
        raise ValueError("Expected repository in owner/name format")

    updates = []
    for version in ("3.12", "3.13", "3.14"):
        variant = "py" + version.replace(".", "")
        path = root / "k8s" / f"deployment-{variant}.yaml"
        original = path.read_text(encoding="utf-8")
        tag = f"py{version}-sha-{sha}"
        image = f"ghcr.io/{repository.lower()}:{tag}"
        content, image_count = re.subn(
            r"(?m)^([ \t]*)image:[ \t]+ghcr\.io/[^\s]+:py"
            + re.escape(version)
            + r"-sha-[0-9a-f]{40}[ \t]*$",
            lambda match: f"{match[1]}image: {image}",
            original,
        )
        content, label_count = re.subn(
            r"(?m)^(\s*)app\.kubernetes\.io/version:[^\r\n]*$",
            lambda match: f'{match[1]}app.kubernetes.io/version: "{tag}"',
            content,
        )
        if image_count != 1 or label_count != 1:
            raise ValueError(
                f"{path}: expected exactly one image and one version label"
            )
        updates.append((path, original, content))

    # Validate every manifest before writing any of them.
    for path, original, content in updates:
        if content != original:
            path.write_text(content, encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", required=True)
    parser.add_argument("--sha", required=True)
    args = parser.parse_args()
    update_images(Path.cwd(), args.repository, args.sha)
