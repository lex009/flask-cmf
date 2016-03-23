from setuptools import setup, find_packages

setup(
    name='Flask CMF',
    version='0.1',
    description='CMF based on Flask Admin',
    author='Alex Belyaev',
    author_email='lex@alexbelyaev.com',
    packages=find_packages(),
    install_requires=[
        'flask-admin>=1.4.0',
        'mongoengine>=0.9.0',
        'babel>=2.1.0',
        'flask-babelex>=0.9.2',
        'blinker>=1.4',
        'flask-mongoengine>=0.7.1',
        'WTForms>=2.0.2',
        'flask-lte-admin>=0.2'
    ],
    dependency_links=[
        'git+git://github.com/lex009/flask-admin-lte#egg=flask-lte-admin-0.2'
    ]
)
