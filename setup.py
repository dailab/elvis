import setuptools
import os

with open("README.md", "r") as fh:
    long_description = fh.read()

try:
    with open('requirements.txt') as req:
        REQUIREMENTS = [r.partition('#')[0] for r in req if not r.startswith('-e')]
except OSError:
    print("Error when reading requirements.txt")
    REQUIREMENTS = []

setuptools.setup(
    name="py-elvis",
    version="0.1.0",
    author="Moritz Markschläger, Jonas Zell, Marcus Voss, Izgh Hadachi",
    author_email="moritz.markschlaeger@dai-labor.de",
    description="A planning and management tool for electric vehicles charging infrastructure",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)