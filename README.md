Vendy is a tool for vendoring third-party packages into your project.

## Disclaimer:
This is not an officially supported Google product.

## Example:

In a `pyproject.toml` file in the root of your package, define the target
directory (should be in the same directory as the `pyproject.toml` file), and
the packages to vendor:

```toml
[tool.vendy]
target = 'my_project'
packages = [
    "sampleproject==1.2.0",
]
```

On the command line:

```
$ python -m vendy
[vendy] Using vendor dir: /private/tmp/my_project/my_project/_vendor
[vendy] Cleaning /private/tmp/my_project/my_project/_vendor
[vendy] Installing vendored libraries
Collecting sampleproject==1.3.0
  Using cached https://files.pythonhosted.org/packages/a1/fd/3564a5176430eac106c27eff4de50b58fc916f5083782062cea3141acfaa/sampleproject-1.3.0-py2.py3-none-any.whl
Installing collected packages: sampleproject
Successfully installed sampleproject-1.3.0
[vendy] Detected vendored libraries: bin, my_data, sample
[vendy] Rewriting all imports related to vendored libs
[vendy] Downloading licenses
Collecting sampleproject==1.3.0
  Using cached https://files.pythonhosted.org/packages/a6/aa/0090d487d204f5de30035c00f6c71b53ec7f613138d8653eebac50f47f45/sampleproject-1.3.0.tar.gz
  Saved ./my_project/_vendor/__tmp__/sampleproject-1.3.0.tar.gz
Successfully downloaded sampleproject
[vendy] Extracting sampleproject-1.3.0/LICENSE.txt into my_project/_vendor/sampleproject.LICENSE.txt
[vendy] Revendoring complete
```

Result:

```
$ tree
.
├── my_project
│   ├── __init__.py
│   └── _vendor
│       ├── bin
│       │   └── sample
│       ├── my_data
│       │   └── data_file
│       ├── sample
│       │   ├── __init__.py
│       │   └── package_data.dat
│       └── sampleproject.LICENSE.txt
└── pyproject.toml
```

And you can import from the vendored library like:

```diff
-from sampleproject.foo import bar
+from myproject._vendor.sampleproject.foo import bar
```
