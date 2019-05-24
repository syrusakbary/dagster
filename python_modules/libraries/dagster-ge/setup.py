import argparse
import sys

from setuptools import find_packages, setup

# pylint: disable=E0401, W0611
if sys.version_info[0] < 3:
    import __builtin__ as builtins
else:
    import builtins


def get_version(name):
    version = {}
    with open("dagster_ge/version.py") as fp:
        exec(fp.read(), version)  # pylint: disable=W0122

    if name == 'dagster-ge':
        return version['__version__']
    elif name == 'dagster-ge-nightly':
        return version['__nightly__']
    else:
        raise Exception('Shouldn\'t be here: bad package name {name}'.format(name=name))


parser = argparse.ArgumentParser()
parser.add_argument('--nightly', action='store_true')


def _do_setup(name='dagster-ge'):
    setup(
        name=name,
        version=get_version(name),
        author='Elementl',
        license='Apache-2.0',
        description='Great Expectations plugin for Dagster',
        url='https://github.com/dagster-io/dagster',
        classifiers=[
            'Programming Language :: Python :: 2.7',
            'Programming Language :: Python :: 3.5',
            'Programming Language :: Python :: 3.6',
            'Programming Language :: Python :: 3.7',
            'License :: OSI Approved :: Apache Software License',
            'Operating System :: OS Independent',
        ],
        packages=find_packages(exclude=['dagster_ge_tests']),
        install_requires=[
            # standard python 2/3 compatability things
            'enum-compat==0.0.2',
            'future>=0.16.0',
            'dagster>=0.2.0',
            'great-expectations>=0.4.2,<=0.5.1',
        ],
    )


if __name__ == '__main__':
    parsed, unparsed = parser.parse_known_args()
    sys.argv = [sys.argv[0]] + unparsed
    if parsed.nightly:
        _do_setup('dagster-ge-nightly')
    else:
        _do_setup('dagster-ge')
