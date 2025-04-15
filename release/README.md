# python_lib/release

This folder contains scripts to orchestrate a release of the
`arcflash` package to [PyPI](https://pypi.org/project/arcflash/).

## How to make a release

Edit `python_lib/make_version_id.py` and change the `RELEASE_VERSION` string.

```
VERSION=0.0.0  # Replace with real version; use rc1 type suffix for testing
git add python_lib/make_version_id.py
git commit -m "Update version"
git tag $VERSION
git push
git push origin $VERSION
```