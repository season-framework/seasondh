import importlib.util
import os
from setuptools import setup, find_packages

SRC_DIR = 'src'
SEASON_PKG_DIR = os.path.join(SRC_DIR, 'seasondh')

spec = importlib.util.spec_from_file_location('version', os.path.join(SEASON_PKG_DIR, 'version.py'))
version = importlib.util.module_from_spec(spec)
spec.loader.exec_module(version)

setup(
    name='seasondh',
    version=version.VERSION_STRING,
    description='A.I. Data Hub',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown', 
    url='https://www.season.co.kr',
    author='proin',
    author_email='proin@season.co.kr',
    license='MIT',
    package_dir={'': SRC_DIR},
    packages=find_packages(SRC_DIR),
    include_package_data=True,
    zip_safe=False,
    install_requires=[],
    python_requires='>=3.6',
    classifiers=[
        'License :: OSI Approved :: MIT License'
    ] 
)