from setuptools import setup, find_packages

setup(
    name="myapp",
    version="1.0",
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            'myapp = myapp.app:main',  # main 함수가 있는 경우
        ],
    },
)
