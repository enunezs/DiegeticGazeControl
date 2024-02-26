from setuptools import find_packages
from setuptools import setup

setup(
    name='diegetic_button_pkg',
    version='0.0.0',
    packages=find_packages(
        include=('diegetic_button_pkg', 'diegetic_button_pkg.*')),
)
