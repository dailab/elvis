import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="elvis-jonaszell97",  # Replace with your own username
    version="0.0.1",
    author="Moritz Markschläger, Jonas Zell",
    author_email="jonas.zell@dai-labor.de",
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