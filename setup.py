from setuptools import setup, find_packages
import versioneer

with open("README.rst") as readme_file:
    readme = readme_file.read()

with open("HISTORY.rst") as history_file:
    history = history_file.read()
    
requirements = [
    # package requirements go here
    "cartopy", 
    "cmocean",
    "matplotlib",
    "oceans",
    "numpy"
]

setup(
    author="Michael Smith",
    author_email='michaesm@marine.rutgers.edu',
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
    description="Helper functions around the Python toolboxes matplotlib for plotting data, and cartopy for plotting data on maps. These functions are written to easily generate maps using some pre-defined settings that our lab prefers to use.",

    install_requires=requirements,
    license="MIT",
    long_description_content_type="text/x-rst",
    long_description=readme + "\n\n" + history,
    include_package_data=True,
    keywords='cool_maps',
    name='cool_maps',
    packages=find_packages(include=['cool_maps', 'cool_maps.*']),
    url='https://github.com/rucool/cool_maps',
    version=versioneer.get_version(),
    cmdclass=versioneer.get_cmdclass(),
    python_requires=">=3.7",
)
