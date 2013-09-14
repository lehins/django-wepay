from distutils.core import setup
import djwepay
import os.path

short_description = 'Django WePay Application.'
long_description = open('README.rst').read() if os.path.isfile('README.rst') \
                   else short_description

setup(
    name='django-wepay',
    version=djwepay.get_version(),
    packages=['djwepay'],
    description=short_description,
    long_description=long_description,
    author='lehins',
    author_email='lehins@yandex.ru',
    license='MIT License',
    url='https://github.com/lehins/django-wepay',
    platforms=["any"],
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ],
)
