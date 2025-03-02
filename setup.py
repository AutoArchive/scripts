from setuptools import setup, find_packages

setup(
    name="ai_archiver",
    version="1.0.0",
    packages=find_packages(where="./"),
    package_dir={"": "./"},
    install_requires=[
        "pyyaml",
        "pandas",
        "requests",
    ],
    python_requires=">=3.6",
) 