from setuptools import find_packages
from setuptools import setup

setup(
    name='fiducials',
    version='0.0.0',
    packages=find_packages(
        include=('fiducials', 'fiducials.*')),
)
