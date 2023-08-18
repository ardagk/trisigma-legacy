from setuptools import setup, find_packages
import glob

packages = find_packages(exclude=['tests','cli', 'cli.*'])
packages.append('tris_cli')

setup(name='trisigma',
      version='1.0.0',
      description='Algo trading SDK',
      author='Arda Gok',
      author_email='ardagkmhs@gmail.com',
      packages=packages,
      package_dir={'tris_cli': 'cli/tris_cli'},
      package_data={
          '': ['exc.toml'],
          '': ['accounts.sql']
      },
      include_package_data=True,
      #install_requires=requirements,
      scripts=glob.glob('scripts/*'),
     )

