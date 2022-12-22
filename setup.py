from setuptools import setup
setup(
    author='Brian Thomas for California Revealed Project',
    author_email='brian.the.archivist@gmail.com',
    description='Converts standardized spreadsheet data and file characterization into sidecar xml at one per folder',
    scripts=['metadata_processor.py', 'crp2.py'],
    license='MIT',
    install_requires=['pandas', 'openpyxl', 'pyexiftool'],
    name='crp2.py',
    version='0.1'
)