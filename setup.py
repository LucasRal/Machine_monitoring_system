from setuptools import setup, find_packages

setup(
    name="machine_monitoring",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        "numpy",
        "python-json-logger",
        "python-dotenv",
        "pandas"
    ]
)