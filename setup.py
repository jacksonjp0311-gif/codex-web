from setuptools import setup, find_packages

setup(
    name="codex-watcher",
    version="0.1.0",
    packages=find_packages(),
    entry_points={
        "console_scripts": [
            "codex-watcher = codex_watcher.cli:main",
            "codex-fetcher = codex_fetcher.fetcher:main",
        ],
    },
    install_requires=[],
    python_requires=">=3.7",
)
