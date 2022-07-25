from setuptools import setup, find_packages

with open("requirements.txt") as f:
	install_requires = f.read().strip().split("\n")

# get version from __version__ variable in sabaintegration/__init__.py
from sabaintegration import __version__ as version

setup(
	name="sabaintegration",
	version=version,
	description="saba",
	author="Ahmad",
	author_email="ahmad@clefincode.com",
	packages=find_packages(),
	zip_safe=False,
	include_package_data=True,
	install_requires=install_requires
)
