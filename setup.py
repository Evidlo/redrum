from setuptools import setup

setup(
    name='imgurt',
    version='1.2.post7',
    packages=['imgurt'],
    author="Evan Widloski",
    author_email="evan@evanw.org",
    description="uses math to select wallpapers from Reddit",
    long_description=open('README.rst').read(),
    license="MIT",
    keywords="imgur reddit wallpaper changer",
    url="https://github.com/evidlo/imgurt",
    entry_points={
        'console_scripts': ['imgurt = imgurt.imgurt:main']
    },
    install_requires=[
        "PyYAML",
        "requests",
    ],
    classifiers=[
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 3"
    ]
)
