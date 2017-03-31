from distutils.core import setup

setup(
    name='imgurt',
    version='1.1',
    packages=['imgurt'],
    author="Evan Widloski",
    author_email="evan@evanw.org",
    description="uses math to select wallpapers from Reddit"
    license="MIT",
    keywords="imgur reddit wallpaper changer",
    url="https://github.com/evidlo/imgurt",
    install_requires=[
        "PyYAML",
        "requests",
        "json",
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
    ]
)
