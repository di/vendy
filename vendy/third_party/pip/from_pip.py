# Original script at:
# https://github.com/pypa/pip/blob/master/tasks/vendoring/__init__.py

from pathlib import Path
import os
import re
import shutil
import subprocess
import tarfile
import zipfile

import click
import requests


def drop_dir(path, **kwargs):
    shutil.rmtree(str(path), **kwargs)


def remove_all(paths):
    for path in paths:
        if path.is_dir():
            drop_dir(path)
        else:
            path.unlink()


def log(msg):
    click.echo("[vendy] %s" % (msg))


def run(command):
    subprocess.call(command.split())


def clean_vendor(config):
    # Old _vendor cleanup
    if not config.vendor_dir.exists():
        return

    log("Cleaning %s" % config.vendor_dir)
    remove_all(config.vendor_dir.glob("*.pyc"))

    for item in config.vendor_dir.iterdir():
        if item.is_dir():
            shutil.rmtree(str(item))
        elif item.name not in config.file_white_list:
            item.unlink()
        else:
            log("Skipping %s" % item)


def detect_vendored_libs(config):
    retval = []
    for item in config.vendor_dir.iterdir():
        if item.is_dir():
            retval.append(item.name)
        elif item.name.endswith(".pyi"):
            continue
        elif "LICENSE" in item.name or "COPYING" in item.name:
            continue
        elif item.name not in config.file_white_list:
            retval.append(item.name[:-3])
    return retval


def rewrite_imports(package_dir, vendored_libs, target):
    for item in package_dir.iterdir():
        if item.is_dir():
            rewrite_imports(item, vendored_libs, target)
        elif item.name.endswith(".py"):
            rewrite_file_imports(item, vendored_libs, target)


def rewrite_file_imports(item, vendored_libs, target):
    """Rewrite 'import xxx' and 'from xxx import' for vendored_libs"""
    text = item.read_text(encoding="utf-8")
    # Revendor pkg_resources.extern first
    text = re.sub(r"pkg_resources\.extern", r"{}._vendor".format(target), text)
    text = re.sub(r"from \.extern", r"from {}._vendor".format(target), text)
    for lib in vendored_libs:
        text = re.sub(
            r"(\n\s*|^)import %s(\n\s*)" % lib,
            r"\1from %s._vendor import %s\2" % (target, lib),
            text,
        )
        text = re.sub(
            r"(\n\s*|^)from %s(\.|\s+)" % lib,
            r"\1from %s._vendor.%s\2" % (target, lib),
            text,
        )
    item.write_text(text, encoding="utf-8")


def apply_patch(patch_file_path):
    log("Applying patch %s" % patch_file_path.name)
    run("git apply --verbose %s" % patch_file_path)


def vendor(config):
    log("Installing vendored libraries")
    # We use --no-deps because we want to ensure that all of our dependencies
    # are added to the packages list, this includes all dependencies
    # recursively up the chain.
    run(
        "pip install -t {0} {1} --no-compile --no-deps".format(
            str(config.vendor_dir), " ".join(config.packages)
        )
    )

    for pattern in config.remove_all:
        remove_all(config.vendor_dir.glob(pattern))

    for path in config.drop_dir:
        drop_dir(config.vendor_dir / path, ignore_errors=True)

    # Detect the vendored packages/modules
    vendored_libs = detect_vendored_libs(config)
    log("Detected vendored libraries: %s" % ", ".join(vendored_libs))

    # Global import rewrites
    log("Rewriting all imports related to vendored libs")
    for item in config.vendor_dir.iterdir():
        if item.is_dir():
            rewrite_imports(item, vendored_libs, config.target)
        elif item.name not in config.file_white_list:
            rewrite_file_imports(item, vendored_libs, config.target)

    # Special cases: apply stored patches
    patch_dir = config.vendor_dir / "_patches"
    patch_files = list(patch_dir.glob("*.patch"))
    if patch_files:
        log("Applying patches")
        for patch in patch_files:
            apply_patch(patch)


def download_licenses(ctx, config):
    log("Downloading licenses")
    tmp_dir = config.vendor_dir / "__tmp__"
    # TODO: get this from the .toml
    run(
        "pip download {0} --no-binary "
        ":all: --no-deps -d {1}".format(" ".join(config.packages), str(tmp_dir))
    )
    for sdist in tmp_dir.iterdir():
        extract_license(ctx, config, sdist)
    drop_dir(tmp_dir)


def extract_license(ctx, config, sdist):
    if sdist.suffixes[-2] == ".tar":
        ext = sdist.suffixes[-1][1:]
        with tarfile.open(sdist, mode="r:{}".format(ext)) as tar:
            found = find_and_extract_license(config, tar, tar.getmembers())
    elif sdist.suffixes[-1] == ".zip":
        with zipfile.ZipFile(sdist) as zip:
            found = find_and_extract_license(config, zip, zip.infolist())
    else:
        raise NotImplementedError("new sdist type!")

    if not found:
        log("License not found in {}, will download".format(sdist.name))
        license_fallback(ctx, config, sdist.name)


def find_and_extract_license(config, tar, members):
    found = False
    for member in members:
        try:
            name = member.name
        except AttributeError:  # zipfile
            name = member.filename
        if "LICENSE" in name or "COPYING" in name:
            if "/test" in name:
                # some testing licenses in html5lib and distlib
                log("Ignoring {}".format(name))
                continue
            found = True
            extract_license_member(config, tar, member, name)
    return found


def license_fallback(ctx, config, sdist_name):
    """Hardcoded license URLs. Check when updating if those are still needed"""
    libname = libname_from_dir(sdist_name)
    if libname not in config.hardcoded_license_urls:
        ctx.fail("License not found for '{}'".format(libname))

    url = config.hardcoded_license_urls[libname]
    _, _, name = url.rpartition("/")
    dest = license_destination(config, libname, name)
    log("Downloading {}".format(url))
    r = requests.get(url, allow_redirects=True)
    r.raise_for_status()
    dest.write_bytes(r.content)


def libname_from_dir(dirname):
    """Reconstruct the library name without it's version"""
    parts = []
    for part in dirname.split("-"):
        if part[0].isdigit():
            break
        parts.append(part)
    return "-".join(parts)


def license_destination(config, libname, filename):
    """Given the (reconstructed) library name, find appropriate destination"""
    normal = config.vendor_dir / libname
    if normal.is_dir():
        return normal / filename
    lowercase = config.vendor_dir / libname.lower()
    if lowercase.is_dir():
        return lowercase / filename
    if libname in config.library_dirnames:
        return config.vendor_dir / config.library_dirnames[libname] / filename
    # fallback to libname.LICENSE (used for nondirs)
    return config.vendor_dir / "{}.{}".format(libname, filename)


def extract_license_member(config, tar, member, name):
    mpath = Path(name)  # relative path inside the sdist
    dirname = list(mpath.parents)[-2].name  # -1 is .
    libname = libname_from_dir(dirname)
    dest = license_destination(config, libname, mpath.name)
    dest_relative = dest.relative_to(Path.cwd())
    log("Extracting {} into {}".format(name, dest_relative))
    try:
        fileobj = tar.extractfile(member)
        dest.write_bytes(fileobj.read())
    except AttributeError:  # zipfile
        dest.write_bytes(tar.read(member))


def update_stubs(ctx):
    config = ctx.obj
    vendored_libs = detect_vendored_libs(config)

    log("Add mypy stubs")

    for lib in vendored_libs:
        if lib not in config.extra_stubs_needed:
            (config.vendor_dir / (lib + ".pyi")).write_text("from %s import *" % lib)
            continue

        for selector in config.extra_stubs_needed[lib]:
            fname = selector.replace(".", os.sep) + ".pyi"
            if selector.endswith(".__init__"):
                selector = selector[:-9]

            f_path = config.vendor_dir / fname
            if not f_path.parent.exists():
                f_path.parent.mkdir()
            f_path.write_text("from %s import *" % selector)


def main(ctx):
    config = ctx.obj
    log("Using vendor dir: %s" % config.vendor_dir)
    clean_vendor(config)
    vendor(config)
    download_licenses(ctx, config)
    log("Revendoring complete")
