from setuptools import setup

setup(
    name='alchemiter',
    version='0.1',
    packages=['alchemiter'],
    entry_points={
        'console_scripts': ['alchemiter = alchemiter.alchemiter:alchemiter']
    }
)
