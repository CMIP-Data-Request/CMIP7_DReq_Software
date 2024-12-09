import io
import os
import re

from setuptools import setup


def read(filename):
    filename = os.path.join(os.path.dirname(__file__), filename)
    text_type = type("")
    with io.open(filename, mode="r", encoding="utf-8") as fd:
        return re.sub(text_type(r":[a-z]+:`~?(.*?)`"), text_type(r"``\1``"), fd.read())


setup(
    name="cmip7_dreq",
    version="0.1.0",  # You should adjust this
    python_requires=">=3.9, <4",
    install_requires=read("requirements.txt").splitlines(),
    packages=["cmip7_dreq"],
    package_dir={"cmip7_dreq": "data_request_api/stable/content/dreq_api"},
    py_modules=["cmip7_dreq"],
)
