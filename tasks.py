import os
import json

from invoke import task
from galaxy.tools import zip_folder_to_file
from fog import buildtools


repo_path = os.path.abspath(os.path.dirname(__file__))


@task
def update_changelog(c, out_dir=repo_path):
    buildtools.update_changelog_file(repo_path=repo_path, out_dir=out_dir)


@task(optional=["output", "ziparchive"])
def build(c, output="output", ziparchive=None):
    buildtools.build(src='src', output=output)

    version = buildtools.load_version(repo_path)
    update_changelog(c, out_dir=output)

    # create manifest
    manifest = {
        "name": "Galaxy Paradox plugin",
        "platform": "paradox",
        "guid": "bfa5a6c9-r0c3-5g28-b921-f4cd75d4999a",
        "version": version,
        "description": "Galaxy Paradox plugin",
        "author": "Friends of Galaxy",
        "email": "friendsofgalaxy@gmail.com",
        "url": "https://github.com/FriendsOfGalaxy/galaxy-integration-paradox",
        "update_url": "https://raw.githubusercontent.com/FriendsOfGalaxy/galaxy-integration-paradox/master/current_version.json",
        "script": "plugin.py"
    }

    with open(os.path.join(output, "manifest.json"), "w") as f:
        json.dump(manifest, f, indent=4)

    if ziparchive is not None:
        zip_folder_to_file(output, ziparchive)


@task
def test(c):
    """Run tests"""
    c.run("pytest --cache-clear")
