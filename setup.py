# Exists to run workflows


from setuptools import setup, find_packages

setup(
    name='energy_monitor',
    version='0.1.0',
    description='tracks the key energy metrics and presents them in a dashbaord',
    author='Joshua',
    packages=find_packages(),
    install_requires=[],
    entry_points={
        'console_scripts': [
            
        ],
    },
    python_requires='>=3.12',
)