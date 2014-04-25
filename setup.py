from setuptools import setup, find_packages
import djwepay
import os.path

short_description = 'Django WePay Application.'
long_description = open('README.rst').read() if os.path.isfile('README.rst') \
                   else short_description

setup(
    name='django-wepay',
    version=djwepay.get_version(),
    packages=find_packages(),
    description=short_description,
    long_description=long_description,
    author='lehins',
    author_email='lehins@yandex.ru',
    license='MIT License',
    url='https://github.com/lehins/django-wepay',
    platforms=["any"],
    install_requires=[
        'python-wepay>=1.3.3',
        'django-json-field>=0.5.5',
    ],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ],
)
