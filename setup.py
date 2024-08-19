# Exists to run workflows


from setuptools import setup, find_packages

setup(
    name='energy_monitor',
    version='0.1.0',
    description='Project description here',
    author='Joshua',
    packages=find_packages(),
    install_requires=[],
    entry_points={
        'console_scripts': [
            # Define any command-line scripts here if needed
        ],
    },
    python_requires='>=3.12',
)