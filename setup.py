from setuptools import setup
from redrum import version
import os
import shutil

module_path = os.path.dirname(os.path.realpath(__file__)) + '/redrum'
config_file = os.path.expanduser('~/.config/redrum.ini')
shutil.copyfile(module_path + '/redrum.ini', config_file)


setup(
    name='redrum',
    version=version.__version__,
    packages=['redrum'],
    author="Evan Widloski",
    author_email="evan@evanw.org",
    description="uses math to select wallpapers from Reddit",
    long_description=open('README.rst').read(),
    long_description_content_type='text/x-rst',
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
