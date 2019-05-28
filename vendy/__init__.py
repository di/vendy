# Copyright 2019 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from pathlib import Path
import os

import click
import toml

from .third_party.pip import from_pip


class Config:
    def __init__(self, config):
        self.config = config

    @property
    def target(self):
        return self.config.get("target")

    @property
    def packages(self):
        return self.config.get("packages", [])

    @property
    def file_white_list(self):
        return self.config.get("file_white_list", [])

    @property
    def library_dirnames(self):
        return self.config.get("library_dirnames", {})

    @property
    def hardcoded_license_urls(self):
        return self.config.get("hardcoded_license_urls", {})

    @property
    def extra_stubs_needed(self):
        return self.config.get("extra_stubs_needed", {})

    @property
    def vendor_dir(self):
        return Path(os.getcwd()) / self.target / "_vendor"

    @property
    def remove_all(self):
        return self.config.get("remove_all", []) + ["*.dist-info", "*.egg-info"]

    @property
    def drop_dir(self):
        return self.config.get("drop_dir", [])


def read_config(ctx):
    try:
        pyproject_toml = toml.load("pyproject.toml")
        config = pyproject_toml.get("tool", {}).get("vendy", {})
    except (toml.TomlDecodeError, OSError):
        ctx.fail(
            "Error reading configuration file: pyproject.toml invalid or misformatted"
        )

    if not config:
        ctx.fail("Error reading configuration file: pyproject.toml not configured")

    config = Config(config)

    if not config.target:
        ctx.fail("Error reading configuration file: 'target' field missing")

    if not config.packages:
        ctx.fail("Error reading configuration file: no packages to vendor")

    return config


@click.group(invoke_without_command=True)
@click.pass_context
def cli(ctx):
    ctx.obj = read_config(ctx)
    from_pip.main(ctx)


@cli.command()
def vendorize():
    pass


@cli.command()
@click.pass_context
def update_stubs(ctx):
    from_pip.update_stubs(ctx)
