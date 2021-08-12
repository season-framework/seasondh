import importlib.util
import os
from setuptools import setup, find_packages

SRC_DIR = 'src'
SEASON_PKG_DIR = os.path.join(SRC_DIR, 'seasondh')
spec = importlib.util.spec_from_file_location('version', os.path.join(SEASON_PKG_DIR, 'version.py'))
version = importlib.util.module_from_spec(spec)
spec.loader.exec_module(version)

def package_files(directory):
    paths = []
    for (path, directories, filenames) in os.walk(directory):
        for filename in filenames:
            paths.append(os.path.join(path, filename)[13:])
    return paths

extra_files = package_files(os.path.join(SEASON_PKG_DIR, 'resources')) + package_files(os.path.join(SEASON_PKG_DIR, 'templates')) + package_files(os.path.join(SEASON_PKG_DIR, 'screenshots'))

setup(
    name='seasondh',
    version=version.VERSION_STRING,
    description='season datahub platform',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown', 
    url='https://github.com/season-framework/seasondh',
    author='proin',
    author_email='proin@season.co.kr',
    license='MIT',
    package_dir={'': SRC_DIR},
    packages=find_packages(SRC_DIR),
    include_package_data=True,
    package_data = {
        'seasondh': extra_files
    },
    zip_safe=False,
    entry_points={'console_scripts': [
        'seasondh = seasondh.cmd:main [seasondh]',
    ]},
    install_requires=[
        'flask',
        'argh',
        'psutil',
        'pypugjs',
        'lesscpy',
        'pymysql',
        'pandas'
    ],
    python_requires='>=3.6',
    classifiers=[
        'License :: OSI Approved :: MIT License'
    ] 
)