from setuptools import setup, find_packages

setup(
    name="whatsapp_warmer",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        'PyQt6',
        'selenium',
        'webdriver-manager',
        'pyqtwebengine'
    ],
    python_requires='>=3.8',
)