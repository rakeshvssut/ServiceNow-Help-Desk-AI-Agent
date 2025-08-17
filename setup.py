# setup.py

from setuptools import setup, find_packages

# Read the contents of your README file
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# Read the contents of your requirements file
with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = fh.read().splitlines()

setup(
    name="atos_agent",
    version="1.0.0",
    author="Rakesh Kumar Sahu",  # You can change this to your name
    author_email="rakeshkumarsahu.tech@gmail.com",  # You can change this to your email
    description="An AI agent for automated ServiceNow ticket routing.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/rakeshvssut/ServiceNow-Help-Desk-AI-Agent",  # Change to your repository URL
    packages=find_packages(),
    install_requires=requirements,
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: System :: Systems Administration",
    ],
    python_requires='>=3.12',
)