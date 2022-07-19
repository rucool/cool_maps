#!/usr/bin/env python

from setuptools import setup, find_packages
import versioneer

with open("README.rst") as readme_file:
    readme = readme_file.read()

with open("HISTORY.rst") as history_file:
    history = history_file.read()

with open("requirements.txt") as requirements_file:
    requirements = requirements_file.read()

test_requirements = [
    "pytest>=3",
]

setup(
    author="Michael Smith",
    author_email='michaesm@marine.rutgers.edu',
    python_requires=">=3.7",
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],   
    description="Helper functions around cartopy for plotting data on maps. These functions are written to easily generate nice-looking maps.",
    install_requires=requirements,
    license="MIT",
    long_description_content_type="text/x-rst",
    long_description=readme + "\n\n" + history,
    include_package_data=True,
    keywords='cool_maps',
    name='cool_maps',
    packages=find_packages(include=['cool_maps', 'cool_maps.*']),
    test_suite="tests",
    tests_require=test_requirements,
    url='https://github.com/rucool/cool_maps',
    version=versioneer.get_version(),
    cmdclass=versioneer.get_cmdclass(),
    zip_safe=False,
    extras_require={},
)
