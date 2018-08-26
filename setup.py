from setuptools import setup
setup(
    author='Kieran O\'Leary for California Revealed Project',
    author_email='kieran.o.leary@gmail.com',
    description="Expresses descriptive and technical metadata in XML",
    scripts=['crp.py'],
    license='MIT',
    install_requires=['lxml'],
    name='crp_dc',
    version='0.13'
)
