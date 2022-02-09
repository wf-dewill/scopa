from setuptools import setup, find_packages

setup(name='Scopa',
      version='1.0',
      description='An Italian Card Game',
      author='Will Farrance',
      setup_requires=['wheel'],
      install_requires=["wheel", "setuptools"],
      include_package_data=True,
      packages=find_packages()
     )