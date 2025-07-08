#!/usr/bin/env python3
"""
CodeRepoIndex 安装脚本
"""

from setuptools import setup, find_packages
import os

# 读取长描述
def read_long_description():
    with open("README.md", "r", encoding="utf-8") as fh:
        return fh.read()

# 读取要求
def read_requirements():
    with open("requirements.txt", "r", encoding="utf-8") as fh:
        return [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="coderepoindex",
    version="0.1.0",
    author="CodeRepoIndex Team",
    author_email="zhongxingyuemail@gmail.com",
    description="通过语义理解提高代码仓库的可发现性和可搜索性",
    long_description=read_long_description(),
    long_description_content_type="text/markdown",
    url="https://github.com/XingYu-Zhong/CodeRepoIndex",
    packages=find_packages(exclude=["tests", "tests.*"]),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Software Development :: Version Control :: Git",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=read_requirements(),
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=22.0.0",
            "flake8>=5.0.0",
            "mypy>=0.950",
        ],
        "docs": [
            "sphinx>=5.0.0",
            "sphinx-rtd-theme>=1.2.0",
            "myst-parser>=0.18.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "coderepoindex=coderepoindex.cli:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
    keywords="code search, vector search, semantic search, code indexing",
    project_urls={
        "Bug Reports": "https://github.com/XingYu-Zhong/CodeRepoIndex/issues",
        "Source": "https://github.com/XingYu-Zhong/CodeRepoIndex",
        "Documentation": "https://coderepoindex.readthedocs.io/",
    },
) 