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

from setuptools import setup

with open("README.md") as f:
    long_description = f.read()

setup(
    name="vendy",
    version="0.0.1",
    author="Dustin Ingram",
    author_email="di@python.org",
    classifiers=[
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
    ],
    install_requires=["click", "requests", "toml"],
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=["vendy"],
    python_requires=">=2.7,!=3.0,!=3.1,!=3.2,!=3.3",
    url="http://github.com/di/vendy",
    description="Vendy is a tool for vendoring third-party packages into your project",
    summary="Vendy is a tool for vendoring third-party packages into your project",
    entry_points={"console_scripts": ["vendy=vendy:cli"]},
)
