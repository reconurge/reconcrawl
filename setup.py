from setuptools import setup, find_packages

setup(
    name="reconcrawl",
    version="0.1.0",
    description="CLI tool and library to extract emails and phone numbers from websites",
    author="EliottElek",
    packages=find_packages(),
    install_requires=[
        "requests",
        "beautifulsoup4",
        "lxml",
    ],
    entry_points={
        "console_scripts": [
            "reconcrawl=reconcrawl.cli:cli",
        ],
    },
    python_requires=">=3.6",
)
