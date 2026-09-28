from setuptools import setup, find_packages

with open("requirements.txt") as f:
    install_requires = f.read().strip().split("\n")

setup(
    name="enzomist",
    version="0.0.1",
    description="Enzomist custom ERPNext app — Kabinart Ghana Ltd",
    author="Kabinart Ghana Ltd",
    author_email="joseph@kabinartghana.com",
    packages=find_packages(),
    zip_safe=False,
    include_package_data=True,
    install_requires=install_requires,
)
