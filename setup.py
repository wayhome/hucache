from setuptools import setup, find_packages
from codecs import open
from os import path

__version__ = "0.0.8"

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, "README.md"), encoding="utf-8") as f:
    long_description = f.read()

# get the dependencies and installs
with open(path.join(here, "requirements.txt"), encoding="utf-8") as f:
    all_reqs = f.read().split("\n")

install_requires = [x.strip() for x in all_reqs if x]

setup(
    name="hucache",
    version=__version__,
    description="A Declarative Caching Library for Human",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/wayhome/hucache",
    license="MIT",
    classifiers=[
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
    ],
    keywords="",
    packages=find_packages(exclude=["docs", "tests*"]),
    include_package_data=True,
    author="wayhome",
    install_requires=install_requires,
    author_email="yanckin@gmail.com",
)
