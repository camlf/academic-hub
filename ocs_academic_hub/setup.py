import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="ocs_academic_hub",
    version="0.87.0",
    author="Christian Foisy",
    author_email="cfoisy@osisoft.com",
    description="OSIsoft Academic Hub Library",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/osisoft/OSI-Samples",
    packages=["ocs_academic_hub"],
    package_dir={"ocs_academic_hub": "ocs_academic_hub"},
    package_data={"ocs_academic_hub": ["*.json"]},
    include_package_data=True,
    # packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
    py_modules=["ocs_academic_hub"],
    install_requires=[
        "pandas>=0.24.2",
        "ocs-sample-library-preview>=0.1.12rc0",
        "numpy",
        "python_dateutil>=2.8.0",
        "typeguard>=2.4.1",
        "gql",
        "backoff",
    ],
    python_requires=">=3.6",
)
