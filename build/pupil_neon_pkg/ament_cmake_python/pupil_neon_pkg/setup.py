from setuptools import find_packages
from setuptools import setup

setup(
    name='pupil_neon_pkg',
    version='1.0.0',
    packages=find_packages(
        include=('pupil_neon_pkg', 'pupil_neon_pkg.*')),
)
