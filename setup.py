from setuptools import setup

setup(
    name="Assistant-Rev",
    version="0.1",

    description="Your AI Assistant - rev",
    author="Surya",
    author_email="dhaneshwarlingam@gmail.com",
    py_modules=["main"],
    entry_points={
        "console_scripts": [
            "rev=main:main",
        ],
    },
)
