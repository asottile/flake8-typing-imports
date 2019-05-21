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
    assert Plugin._min_python_version == Version(3, 6)


def test_option_parsing_python_requires_more_complicated(tmpdir):
    tmpdir.join('setup.cfg').write(
        '[options]\n'
        'python_requires = >=2.7, !=3.0.*, !=3.1.*, !=3.2.*, !=3.3.*',
    )
    Plugin.parse_options(mock.Mock(min_python_version='3.6.0'))
    assert Plugin._min_python_version == Version(3, 5)


def test_option_parsing_minimum_version():
    Plugin.parse_options(mock.Mock(min_python_version='3.4'))
    assert Plugin._min_python_version == Version(3, 5)


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
