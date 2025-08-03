"""
Setup configuration for Polymarket Data Extractor.
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read the README file
readme_path = Path(__file__).parent / "README.md"
long_description = readme_path.read_text() if readme_path.exists() else ""

setup(
    name="polymarket-data",
    version="1.0.0",
    author="Polymarket Data Team",
    description="A Python library for extracting historical price data from Polymarket prediction markets",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/polymarket-data",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Financial and Insurance Industry",
        "Topic :: Office/Business :: Financial :: Investment",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.9",
    install_requires=[
        "httpx>=0.25.0",
        "pandas>=2.0.0",
        "tabulate>=0.9.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "isort>=5.12.0",
            "mypy>=1.5.0",
            "flake8>=6.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "polymarket-extract=polymarket_extract:main",
            "mango=mango_cli:main",
        ],
    },
    project_urls={
        "Bug Reports": "https://github.com/yourusername/polymarket-data/issues",
        "Source": "https://github.com/yourusername/polymarket-data",
    },
)