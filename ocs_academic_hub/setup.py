import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="ocs_academic_hub",
    version="0.65.0",
    author="Christian Foisy",
    author_email="cfoisy@osisoft.com",
    description="OSIsoft Academic Hub support package",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/osisoft/OSI-Samples",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
    py_modules=["ocs_academic_hub"],
        install_requires=[
            "pandas>=0.24.2", 
            "ocs-sample-library-preview==0.1.4rc0",
            "numpy", 
            "python_dateutil>=2.8.0",
            "typeguard>=2.4.1"
    ],
    python_requires='>=3.6'
)
