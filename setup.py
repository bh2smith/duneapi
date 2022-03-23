import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="duneapi",
    version="2.0.4",
    author="Benjamin H. Smith",
    author_email="bh2smith@gmail.com",
    description="A simple framework for interacting with Dune Analytics' unsupported API.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/bh2smith/duneapi",
    project_urls={
        "Bug Tracker": "https://github.com/bh2smith/duneapi/issues",
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
    install_requires=["requests>=2.27.1", "types-requests>=2.27.13"],
    package_dir={"": "src"},
    packages=setuptools.find_packages(where="src"),
    package_data={
        "duneapi": ["py.typed"],
    },
    python_requires=">=3.9",
)
