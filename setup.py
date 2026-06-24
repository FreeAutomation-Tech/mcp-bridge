from setuptools import setup, find_packages

setup(
    name="mcp-bridge",
    version="0.1.0",
    packages=find_packages("src"),
    package_dir={"": "src"},
    entry_points={
        "console_scripts": [
            "mcp-bridge=mcp_bridge.cli:main",
        ],
    },
    python_requires=">=3.9",
    install_requires=[],
)
