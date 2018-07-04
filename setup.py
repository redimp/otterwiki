from setuptools import setup, find_packages

with open('requirements.txt') as f:
        requirements = f.read().splitlines()

setup(
    name='otterwiki',
    version='0.1',
    long_description=__doc__,
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    install_requires=requirements,
    extras_require={
        'dev': [
            'coverage',
        ]
    }
)
