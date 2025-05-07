from setuptools import setup

setup(
    name='md5_modifier',
    version='1.0',
    scripts=['md5_modifier.py'],
    install_requires=[
        'pillow>=10.0.0',
        'pyinstaller>=6.0.0'
    ],
    python_requires='>=3.8',
    entry_points={
        'console_scripts': [
            'md5tool = md5_modifier:main'
        ]
    }
)