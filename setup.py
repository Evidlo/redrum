from setuptools import setup

setup(
    name='redrum',
    version='1.4.8',
    packages=['redrum'],
    package_data={'redrum': ['redrum.ini']},
    author="Evan Widloski",
    author_email="evan@evanw.org",
    description="uses math to select wallpapers from Reddit",
    long_description=open('README.rst').read(),
    license="MIT",
    keywords="Reddit wallpaper changer",
    url="https://github.com/evidlo/redrum",
    entry_points={
        'console_scripts': ['redrum = redrum.redrum:main']
    },
    install_requires=[
        "PyYAML",
        "requests",
        "configparser"
    ],
    classifiers=[
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 3"
    ]
)
