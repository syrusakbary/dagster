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
    with open("dagstermill/version.py") as fp:
        exec(fp.read(), version)  # pylint: disable=W0122

    if name == 'dagstermill':
        return version['__version__']
    elif name == 'dagstermill-nightly':
        return version['__nightly__']
    else:
        raise Exception('Shouldn\'t be here: bad package name {name}'.format(name=name))


parser = argparse.ArgumentParser()
parser.add_argument('--nightly', action='store_true')


def _do_setup(name='dagstermill'):
    setup(
        name=name,
        version=get_version(name),
        author='Elementl',
        license='Apache-2.0',
        packages=find_packages(exclude=['dagstermill_tests']),
        classifiers=[
            'Programming Language :: Python :: 2.7',
            'Programming Language :: Python :: 3.5',
            'Programming Language :: Python :: 3.6',
            'Programming Language :: Python :: 3.7',
            'License :: OSI Approved :: Apache Software License',
            'Operating System :: OS Independent',
        ],
        install_requires=[
            # standard python 2/3 compatability things
            'dagster-pandas',
            'enum-compat==0.0.2',
            'future>=0.16.0, <0.17.0a0',
            'ipykernel>=4.9.0',
            'nteract-scrapbook>=0.2.0',
            'papermill>=1.0.0',
            'scikit-learn==0.20.3',
        ],
        entry_points={"console_scripts": ['dagstermill = dagstermill.cli:main']},
    )


if __name__ == '__main__':
    parsed, unparsed = parser.parse_known_args()
    sys.argv = [sys.argv[0]] + unparsed
    if parsed.nightly:
        _do_setup('dagstermill-nightly')
    else:
        _do_setup('dagstermill')
