from setuptools import setup, find_packages

setup(
    name='analitiq',
    version='0.1.0',
    author='Kirill Andriychuk',
    author_email='support@analitiq.ai',
    packages=['analitiq'],
    entry_points={
        'console_scripts': [
            'run=analitiq.cli_runner:main',
        ],
    },
    install_requires=[
        'requests',
        'pandas>=1.0.0',
        'langchain'
    ],
    # Include package data to ensure that non-code files (like your README) are included
    include_package_data=True,
    description='A brief description of your package',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/analitiq-ai',
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.9',
)
