from setuptools import setup, find_packages

setup(
    name="content-aggregator-shared",
    version="0.1.0",
    description="Shared modules for content aggregator projects (001, 003, etc.)",
    packages=find_packages(),
    install_requires=[
        "fastapi>=0.100.0",
        "pyjwt>=2.8.0",
        "httpx>=0.27.0",
        "cryptography>=42.0.0",
        "pydantic>=2.0.0",
        "playwright>=1.48.0",
        "loguru>=0.7.2",
    ],
    python_requires=">=3.12",
)
