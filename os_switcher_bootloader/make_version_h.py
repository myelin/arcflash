import datetime
import os
import re
import sys

def get_version():
    channel, = sys.argv[1:]

    if channel == 'dev':
        return datetime.datetime.now().strftime('%Y-%m-%d')

    if channel == 'release':
        print("Making release version", file=sys.stderr)
        gh_ref = os.environ.get("GITHUB_TAG")
        if gh_ref:
            print(f"Have a GitHub ref: {gh_ref}", file=sys.stderr)
            m = re.fullmatch(r"^refs/tags/(.*?)$", gh_ref)
            if m:
                tag_name = m.group(1)
                print(f"It's a release tag: {tag_name}", file=sys.stderr)
                return tag_name

    # Release build with no tag; use the short hash instead.
    short_hash = os.popen("git rev-parse --short HEAD", "r").read().strip()
    return short_hash

version = get_version()

print(f'''#define ARCFLASH_BUILD_VERSION "{version}"''')
