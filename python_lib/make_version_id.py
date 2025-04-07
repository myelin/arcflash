import datetime
import os
import re
import sys


RELEASE_VERSION = "0.2.0"


def get_version(channel="release"):

    if channel == "dev":
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        return f"{RELEASE_VERSION}+{today}"

    if channel == "release":
        print("Making release version", file=sys.stderr)
        gh_ref = os.environ.get("GITHUB_TAG")
        if gh_ref:
            # Tag names override RELEASE_VERSION, although it should
            # always be updated around the same time, so local versions
            # stay in sync.
            print(f"Have a GitHub ref: {gh_ref}", file=sys.stderr)
            m = re.fullmatch(r"^refs/tags/(.*?)$", gh_ref)
            if m:
                tag_name = m.group(1)
                print(f"It's a release tag: {tag_name}", file=sys.stderr)
                return tag_name

    # Release build with no tag; use the short hash instead.
    short_hash = os.popen("git rev-parse --short HEAD", "r").read().strip()
    return f"{RELEASE_VERSION}+{short_hash}"


if __name__ == "__main__":
    # Run as a script, to get header file contents for firmware and boot menu.
    (channel,) = sys.argv[1:]
    version = get_version(channel)
    print(f'''#define ARCFLASH_BUILD_VERSION "{version}"''')
