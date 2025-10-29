#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import find_packages, setup


setup(
    name="pip-fc",
    version="0.1.6",
    description="轻量级 Python 工具，用于测试多个镜像源的连接速度",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="HarmonSir",
    author_email="git@pylab.me",
    url="https://github.com/harmonsir/pip-fc",
    packages=find_packages(),
    install_requires=[
        # "futures",  # 仅针对 Python 2.7 需要
    ],
    classifiers=[
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    entry_points={
        "console_scripts": [
            "pip-fc = pip_fc.core:entry_point",
        ],
    },
    # PyPI 发布包文件名格式支持
    python_requires=">=2.7, <4",
    keywords="mlc-mirror mirror speed pip",
)
