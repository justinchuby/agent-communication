from setuptools import setup, find_packages

setup(
    name="textanalyzer",
    version="0.1.0",
    description="A text analysis library with CLI for word frequency, sentiment, and statistics",
    packages=find_packages(),
    python_requires=">=3.10",
    entry_points={
        "console_scripts": [
            "textanalyzer=textanalyzer.cli.main:main",
        ],
    },
)
