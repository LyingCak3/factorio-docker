#!/usr/bin/env python3

import argparse
import os
import json
import subprocess
import shutil
import sys
import tempfile

def build_dockerfile(sha256, version, tags):
    build_dir = tempfile.mktemp()
    shutil.copytree("docker", build_dir)

    build_command = ["docker", "build", "--build-arg", f"VERSION={version}",
                     "--build-arg", f"SHA256={sha256}", "."]
    for tag in tags:
        build_command.extend(["-t", f"factoriotools/factorio:{tag}"])
    try:
        subprocess.run(build_command, cwd=build_dir, check=True)
    except subprocess.CalledProcessError:
        print("Build of image failed")
        exit(1)


def login():
    try:
        username = os.environ["DOCKER_USERNAME"]
        password = os.environ["DOCKER_PASSWORD"]
        subprocess.run(["docker", "login", "-u", username, "-p", password], check=True)
    except KeyError:
        print("Username and password need to be given")
        exit(1)
    except subprocess.CalledProcessError:
        print("Docker login failed")
        exit(1)


def main(sargs):
    with open(os.path.join(os.path.dirname(__file__), "buildinfo.json")) as file_handle:
        builddata = json.load(file_handle)

    avail_tags = [ tag for builditem in builddata.values() for tag in builditem["tags"] ]

    parser = argparse.ArgumentParser()
    
    parser.add_argument("--push-tags", action="store_true", dest="push_tags", help="Push tags to docker repo.", default=False)
    parser.add_argument("--tags", nargs="+", default=avail_tags, help="Tags to build [Default: %(default)s]")

    args = parser.parse_args(args=sargs)

    if args.push_tags:
        login()

    for version, buildinfo in builddata.items():
        sha256 = buildinfo["sha256"]
        tags = [ tag for tag in buildinfo["tags"] if tag in args.tags ]
        if 0 == len(tags):
            continue
        build_dockerfile(sha256, version, tags)
        if not args.push_tags:
            continue
        for tag in tags:
            try:
                subprocess.run(["docker", "push", f"factoriotools/factorio:{tag}"],
                               check=True)
            except subprocess.CalledProcessError:
                print("Docker push failed")
                exit(1)


if __name__ == '__main__':
    main(sys.argv[1:])
