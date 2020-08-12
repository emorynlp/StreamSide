import setuptools

with open('README.md') as fh:
    long_description = fh.read()

setuptools.setup(
    name='streamside',
    version='0.1',
    scripts=[],
    author='Jinho D. Choi',
    author_email='jinho.choi@emory.edu',
    description='Semantic Network Annotation Toolkit',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/emorynlp/StreamSide',
    packages=setuptools.find_packages(),
    install_requires=[
         'PyQt5==5.15.0'
     ],
     classifiers=[
         'Programming Language :: Python :: 3',
         'License :: OSI Approved :: Apache License 2.0',
         'Operating System :: OS Independent',
     ],
    package_data={'streamside': ['resources/*/*.json']},
    include_package_data=True
 )