from setuptools import setup, find_packages

setup(
    name="hls_manifest",
    version="0.1",
    packages=find_packages(),
    install_requires=["click", "jsonschema"],
    include_package_data=True,
    extras_require={"dev": ["flake8", "black"], "test": ["flake8", "pytest"]},
    entry_points={"console_scripts": ["create_manifest=hls_manifest.hls_manifest:main", ]},
)
