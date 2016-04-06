from setuptools import setup, find_packages
from pyqt_distutils.build_ui import build_ui
cmdclass = {'build_ui': build_ui}

setup(
    name = "piccolo2-player",
    version = "0.1",
    namespace_packages = ['piccolo2'],
    packages = find_packages(),
    install_requires = [
        "piccolo2-client",
    ],
    entry_points={
        'gui_scripts': [
            'piccolo2-player = piccolo2.pplayer:main',
        ],
    },
    cmdclass=cmdclass,

    # metadata for upload to PyPI
    author = "Magnus Hagdorn, Alasdair MacArthur, Iain Robinson",
    description = "Part of the piccolo2 system. This package provides GUI client",
    license = "GPL",
    url = "https://bitbucket.org/uoepiccolo/piccolo2-player",
)
