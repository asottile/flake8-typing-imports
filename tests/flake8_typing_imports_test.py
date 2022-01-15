from __future__ import annotations

import ast
from unittest import mock

import pytest
from flake8.options.manager import OptionManager

from flake8_typing_imports import Plugin
from flake8_typing_imports import Version


def version_ctx(v):
    return mock.patch.object(Plugin, '_min_python_version', v)


@pytest.fixture(autouse=True)
def reset_version(tmpdir):
    with version_ctx(Plugin._min_python_version), tmpdir.as_cwd():
        yield


def test_option_parsing():
    mgr = OptionManager('flake8', '0')
    Plugin.add_options(mgr)
    options, _ = mgr.parse_args(['--min-python-version', '3.6.2'])
    Plugin.parse_options(options)
    assert Plugin._min_python_version == Version(3, 6, 2)


def test_option_parsing_python_requires_setup_cfg(tmpdir):
    tmpdir.join('setup.cfg').write('[options]\npython_requires = >=3.6')
    Plugin.parse_options(mock.Mock(min_python_version='3.5.0'))
    assert Plugin._min_python_version == Version(3, 6, 0)


def test_option_parsing_python_requires_more_complicated(tmpdir):
    tmpdir.join('setup.cfg').write(
        '[options]\n'
        'python_requires = >=2.7, !=3.0.*, !=3.1.*, !=3.2.*, !=3.3.*',
    )
    Plugin.parse_options(mock.Mock(min_python_version='3.6.0'))
    assert Plugin._min_python_version == Version(3, 5, 0)


def test_option_parsing_minimum_version():
    Plugin.parse_options(mock.Mock(min_python_version='3.4'))
    assert Plugin._min_python_version == Version(3, 5, 0)


def test_option_parsing_error_unknown():
    with pytest.raises(ValueError) as excinfo:
        Plugin.parse_options(mock.Mock(min_python_version='9.9'))
    msg, = excinfo.value.args
    assert msg == 'min-python-version (9.9.0): unknown version'


def results(s):
    return {'{}:{}: {}'.format(*r) for r in Plugin(ast.parse(s)).run()}


def test_missing_guard():
    with version_ctx(Version(3, 5, 0)):
        assert results('from typing import Type') == {
            '1:0: TYP001 guard import by `if False:  # TYPE_CHECKING`: Type '
            '(not in 3.5.0, 3.5.1)',
        }


def test_missing_guard_3_5_1():
    with version_ctx(Version(3, 5, 1)):
        assert results('from typing import Type') == {
            '1:0: TYP001 guard import by `if False:  # TYPE_CHECKING`: Type '
            '(not in 3.5.1)',
        }


def test_guard_by_False():
    ret = results(
        'if False:\n'
        '    from typing import Type',
    )
    assert ret == set()


def test_guard_by_assignment():
    ret = results(
        'MYPY = False\n'
        'if MYPY:\n'
        '    from typing import Type',
    )
    assert ret == set()


def test_guard_by_type_checking():
    with version_ctx(Version(3, 7, 0)):
        ret = results(
            'from typing import TYPE_CHECKING\n'
            'if TYPE_CHECKING:\n'
            '    from typing import DEFINITELY_WRONG\n',
        )
        assert ret == set()


def test_relative_typing_module():
    ret = results('from .typing import wat')
    assert ret == set()


def test_missing_overload_define():
    with version_ctx(Version(3, 5, 0)):
        ret = results('from typing import overload')
        assert ret == {
            '1:0: TYP002 @overload is broken in <3.5.2, '
            'add `if sys.version_info < (3, 5, 2): def overload(f): return f`',
        }
        assert not results(
            'import sys\n'
            'from typing import overload\n'
            'if sys.version_info < (3, 5, 2):\n'
            '    def overload(f):\n'
            '        return f\n'
            '@overload\n'
            'def f(x): pass\n',
        )
    with version_ctx(Version(3, 5, 2)):
        assert not results('from typing import overload')


@pytest.mark.parametrize(
    's', (
        pytest.param(
            'from typing import Pattern, Union\n'
            'def foo(bar: Union[Pattern, str]): pass\n',
            id='Pattern',
        ),
        pytest.param(
            'import typing\n'
            'def foo(bar: typing.Union[typing.Pattern, str]): pass\n',
            id='typing.Pattern',
        ),
        pytest.param(
            'from typing import Match, Union\n'
            'def foo(bar: Union[Match, str]): pass\n',
            id='Match',
        ),
        pytest.param(
            'import typing\n'
            'def foo(bar: typing.Union[typing.Match, str]): pass\n',
            id='typing.Match',
        ),
        pytest.param(
            'from typing import Match, Pattern, Union\n'
            'def foo(bar: Union[Match, Pattern, int]): pass\n',
            id='Match and Pattern',
        ),
        pytest.param(
            'from typing import Match as M, Union\n'
            'def foo(bar: Union[M, str]): pass\n',
            id='Match imported as Name',
            marks=pytest.mark.xfail(
                reason=(
                    'this is broken too, but so unlikely we elect not to '
                    'detect it'
                ),
            ),
        ),
    ),
)
def test_union_pattern_or_match(s):
    with version_ctx(Version(3, 5, 0)):
        assert results(s) == {
            '2:13: TYP003 Union[Match, ...] or Union[Pattern, ...] '
            'must be quoted in <3.5.2',
        }

    with version_ctx(Version(3, 5, 2)):
        assert not results(s)


@pytest.mark.parametrize(
    's', (
        pytest.param(
            'from bar import Bar\n'
            'def foo(bar: Union[Bar]): pass\n',
            id='neither Pattern, nor Match',
        ),
        pytest.param(
            'from typing import Pattern, Union\n'
            'def foo(bar: Union[Pattern]): pass\n',
            id='single Pattern',
        ),
        pytest.param(
            'from typing import Pattern, Union\n'
            'def foo(bar: "Union[Pattern, str]"): pass\n',
            id='quoted Pattern',
        ),
        pytest.param(
            'from typing import Match, Union\n'
            'def foo(bar: "Union[Match, str]"): pass\n',
            id='quoted Match',
        ),
        pytest.param(
            'from typing import Union\n'
            'Union[1:2]\n',
            id='unrelated, but covers non-slice case',
        ),
    ),
)
def test_union_pattern_or_match_noop(s):
    assert not results(s)


def test_namedtuple_methods():
    s = (
        'from typing import NamedTuple\n'
        'class NT(NamedTuple):\n'
        '    x: int\n'
        '    def f(self): return self.x + 2\n'
    )
    with version_ctx(Version(3, 6, 0)):
        assert results(s) == {
            '4:4: TYP004 NamedTuple does not support methods in 3.6.0',
        }

    with version_ctx(Version(3, 6, 1)):
        assert results(s) == set()


def test_namedtuple_defaults():
    s = (
        'from typing import NamedTuple\n'
        'class NT(NamedTuple):\n'
        '    x: int = 5\n'
    )
    with version_ctx(Version(3, 6, 0)):
        assert results(s) == {
            '3:4: TYP005 NamedTuple does not support defaults in 3.6.0',
        }

    with version_ctx(Version(3, 6, 1)):
        assert results(s) == set()


def test_namedtuple_check_noop():
    s = (
        'class C:\n'
        '    x: int = 2\n'
        '    def f(self): return self.x + 5\n'
    )
    assert not results(s)


def test_attribute():
    s = (
        'import typing\n\n'
        'def f() -> typing.Type:\n'
        '    pass\n'
    )
    with version_ctx(Version(3, 5, 0)):
        assert results(s) == {
            '3:11: TYP006 guard `typing` attribute by quoting: Type '
            '(not in 3.5.0, 3.5.1)',
        }
