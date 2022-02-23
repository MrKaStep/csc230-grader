import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="grader",
    version="0.0.1",
    author="Stepan Kalinin",
    author_email="skalini@ncsu.edu",
    description="Grader for CSC230",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/MrKaStep/csc230-grader",
    project_urls={
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    package_dir={"": "src"},
    packages=setuptools.find_packages(where="src"),
    python_requires=">=3.6",
)
