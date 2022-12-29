[![build status](https://github.com/asottile/flake8-typing-imports/actions/workflows/main.yml/badge.svg)](https://github.com/asottile/flake8-typing-imports/actions/workflows/main.yml)
[![pre-commit.ci status](https://results.pre-commit.ci/badge/github/asottile/flake8-typing-imports/main.svg)](https://results.pre-commit.ci/latest/github/asottile/flake8-typing-imports/main)

flake8-typing-imports
=====================

flake8 plugin which checks that typing imports are properly guarded

## installation

```bash
pip install flake8-typing-imports
```

## flake8 codes

| Code   | Description                                                           |
|--------|-----------------------------------------------------------------------|
| TYP001 | guard import by `TYPE_CHECKING`                                       |
| TYP002 | `@overload` is broken in <3.5.2                                       |
| TYP003 | `Union[Match, ...]` or `Union[Pattern, ...]` must be quoted in <3.5.2 |
| TYP004 | `NamedTuple` does not support methods in 3.6.0                        |
| TYP005 | `NamedTuple` does not support defaults in 3.6.0                       |
| TYP006 | guard `typing` attribute by quoting                                   |

## rationale

unfortunately, the `typing` module has been pretty unstable -- it has seen api
changes in 3.5.0, 3.5.2, 3.5.3, 3.5.4, 3.6.0, 3.6.1, 3.6.2, 3.7.0, and 3.7.2!

depending on your supported version of python, you may need to guard your
imports by `if TYPE_CHECKING:` (3.5.2+) or `if False:` if the things you are
importing aren't available in all the pythons you support.

as it's pretty difficult to keep track of what version things changed and you
can't always test against particular patch versions of python, this plugin
helps you statically check this automatically!

```python
# default / --min-python-version 3.5.0
from typing import Type  # TYP001
```

```python
# default / --min-python-version 3.5.0
if False:
    from typing import Type  # OK!
```

```python
# default / --min-python-version 3.5.0
from typing import overload  # TYP002
```

```python
# default / --min-python-version 3.5.0
import sys
from typing import overload  # OK!
if sys.version_info < (3, 5, 2):
    def overload(f):
        return f
```

```python
# default / --min-python-version 3.5.0
def foo(bar: Union[Match, str]) -> None: pass  # TYP003
def foo(bar: "Union[Match, str]") -> None: pass  # OK!

def foo(bar: Union[Pattern, str]) -> None: pass  # TYP003
def foo(bar: "Union[Pattern, str]") -> None: pass  # OK!
```

```python
# --min-python-version 3.6.0
class NT(NamedTuple):
    x: int = 5  # TYP005

    def f(self) -> int:  # TYP004
        return self.x + 4
```

```python
# --min-python-version 3.7.0
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from typing import OrderedDict  # OK!
```

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
-   repo: https://github.com/pycqa/flake8
    rev: 3.7.7
    hooks:
    -   id: flake8
        additional_dependencies: [flake8-typing-imports==1.12.0]
```
