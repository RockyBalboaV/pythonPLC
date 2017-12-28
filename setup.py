from setuptools import setup, find_packages

requirements = [
    'celery',
    'redis',
    'python-snap7',
    'requests',
    'celery_once',
    'sqlalchemy',
    'pytest',
    'flower',
    'psutil',
    'eventlet',
    'dnspython',
    'pymysql'
]

setup(
    name='pyplc_client',
    version='1.0.0',
    packages=find_packages(),
    install_requires=requirements,
)