from setuptools import setup
from redrum import version
import os

config_file = os.path.expanduser('~/.config/redrum.ini')

setup(
    name='redrum',
    version=version.__version__,
    packages=['redrum'],
    author="Evan Widloski",
    author_email="evan@evanw.org",
    description="uses math to select wallpapers from Reddit",
    long_description=open('README.rst').read(),
    license="MIT",
    keywords="Reddit wallpaper changer",
    url="https://github.com/evidlo/redrum",
    data_files = [(os.path.dirname(config_file), ['redrum/redrum.ini'])],
    entry_points={
        'console_scripts': ['redrum = redrum.redrum:main',
                            'redrum_tune = redrum.tune_gui:main [tune]'
        ]
    },
    install_requires=[
        "PyYAML",
        "requests",
        "configparser"
    ],
    extras_require={
        'tune': ['matplotlib', 'numpy']
    },
    classifiers=[
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 3"
    ]
)
