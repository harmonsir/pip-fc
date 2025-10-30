#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import find_packages, setup


setup(
    name="pip-fc",  # 包名称
    version="0.1.9",  # 版本号
    description="一款轻量级的 Python 工具，用于高效测试多个镜像源的连接速度，帮助用户选择最优的镜像源以提高包管理效率。",
    # 简短描述
    long_description=open("README.md").read(),  # 详细描述，加载 README.md 文件
    long_description_content_type="text/markdown",  # Markdown 格式
    author="HarmonSir",  # 作者
    author_email="git@pylab.me",  # 作者邮箱
    url="https://github.com/harmonsir/pip-fc",  # 项目 GitHub 地址
    packages=find_packages(),  # 自动发现包
    install_requires=[  # 安装依赖
        # "futures",  # 仅针对 Python 2.7 需要
    ],
    classifiers=[  # 分类信息
        "Programming Language :: Python :: 2.7",  # 支持的 Python 版本
        "Programming Language :: Python :: 3",  # 支持的 Python 版本
        "License :: OSI Approved :: MIT License",  # 开源许可
        "Operating System :: OS Independent",  # 操作系统无关
    ],
    entry_points={  # 设置命令行入口
        "console_scripts": [
            "pip-fc = pip_fc.core:entry_point",  # pip-fc 命令对应的函数
        ],
    },
    # PyPI 发布包文件名格式支持
    python_requires=">=2.7, <4",  # 支持的 Python 版本范围
    keywords="mlc-mirror mirror speed pip",  # 关键字
)
