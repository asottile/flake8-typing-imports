[![Build Status](https://dev.azure.com/asottile/asottile/_apis/build/status/asottile.flake8-typing-imports?branchName=master)](https://dev.azure.com/asottile/asottile/_build/latest?definitionId=23&branchName=master)
[![Azure DevOps coverage](https://img.shields.io/azure-devops/coverage/asottile/asottile/23/master.svg)](https://dev.azure.com/asottile/asottile/_build/latest?definitionId=23&branchName=master)

flake8-typing-imports
=====================

flake8 plugin which checks that typing imports are properly guarded

## installation

`pip install flake8-typing-imports`

## rationale

depending on your supported version of python, you may need to guard your
imports by `if TYPE_CHECKING:` (3.5.2+) or `if False:` if the things you are
importing aren't available in all the pythons you support.

unfortunately, the `typing` module has been pretty unstable -- it has seen api
changes in 3.5.0, 3.5.2, 3.5.3, 3.5.4, 3.6.0, 3.6.1, 3.6.2, and 3.7.0!

as it's pretty difficult to keep track of what version things changed and you
can't always test against particular patch versions of python, this plugin
helps you statically check this automatically!

## configuration

this plugin has a single configuration point (beyond those provided by flake8)
which is the `--min-python-version` option.

by default, this option is `3.5.0`.  this includes all versions of python
which have the `typing` module present.

you can also set this option in the flake8 configuration if you don't want
to use the commandline:

```ini
[flake8]
min_python_version = 3.6.2
```

if a `>=` is set for `python_requires` in `setup.cfg`, that value will be used:

```ini
# setup.cfg setuptools metadata

[options]
python_requires = >=3.6
```

## as a pre-commit hook

See [pre-commit](https://github.com/pre-commit/pre-commit) for instructions

Sample `.pre-commit-config.yaml`:

```yaml
-   repo: https://gitlab.com/pycqa/flake8
    rev: 3.7.7
    hooks:
    -   id: flake8
        additional_dependencies: [flake8-typing-imports==1.0.0]
```
