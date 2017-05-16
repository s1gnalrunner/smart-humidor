from setuptools import setup, find_packages

setup(
    name='smart_humidor',
    use_scm_version=True,
    setup_requires=['setuptools_scm'],
    packages=find_packages(),
    url='',
    license='',
    author='',
    author_email='',
    description='',
    entry_points={
          'console_scripts': [
              'sh-sensor = smart_humidor.sensor:main',
              'sh-lcd = smart_humidor.lcd:main',
          ]
    },
)
