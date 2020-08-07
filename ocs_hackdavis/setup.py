import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="ocs_hackdavis",
    version="0.44.0",
    author="Christian Foisy",
    author_email="cfoisy@osisoft.com",
    description="OSIsoft HackDavis 2020 package",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/osisoft/OSI-Samples",
    packages=['ocs_hackdavis'],
    package_dir={'ocs_hackdavis': 'src/ocs_hackdavis'},
    package_data={
        'ocs_hackdavis': ['*.yaml'],
    },
    include_package_data=True,
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
    # py_modules=["ocs_hackdavis"],
    install_requires=[
        "typeguard>=2.4.1",
        "ocs-academic-hub>=0.70.0",
        "python-dateutil>=2.8.0",
        "backoff",
        "pyyaml",
    ],
    python_requires='>=3.6'
)
