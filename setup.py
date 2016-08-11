from setuptools import setup

setup(
    name='appeldryck',
    version='0.1',
    packages=['appeldryck'],
    entry_points={
        'console_scripts': ['dryck = appeldryck.appeldryck:appeldryck']
    }
)
