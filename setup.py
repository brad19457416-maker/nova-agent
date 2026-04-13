from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="nova-agent",
<<<<<<< HEAD
    version="0.3.0",
=======
    version="0.2.0",
>>>>>>> fffb151 (P0 improvements: add .gitignore, GitHub Actions CI, bump version to v0.2.0)
    author="Nova Agent Team",
    description="新一代自主智能体 —— 融合五大前沿开源项目精华，专为 OpenClaw 设计",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/brad19457416-maker/nova-agent",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
    python_requires=">=3.9",
    install_requires=[
        "langgraph>=0.0.10",
        "langchain>=0.1.0",
        "chromadb>=0.4.0",
        "sentence-transformers>=2.2.0",
        "pyyaml>=6.0",
        "docker>=6.0.0",
        "requests>=2.26.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0",
            "pytest-cov>=4.0",
            "black>=22.0",
            "ruff>=0.1.0",
            "mypy>=1.0",
            "build>=0.10",
            "twine>=4.0",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)
