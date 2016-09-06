#!/usr/bin/env python
import re
import os
import uuid
from setuptools import setup, find_packages
from pip.req import parse_requirements

src_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), "src")

VERSION_FILE = os.path.join(src_path, "sensetdp", "__init__.py")
ver_file = open(VERSION_FILE, "rt").read()
VERSION_RE = r"^__version__ = ['\"]([^'\"]*)['\"]"
mo = re.search(VERSION_RE, ver_file, re.M)

if mo:
    version = mo.group(1)
else:
    raise RuntimeError("Unable to find version string in %s." % (VERSION_FILE,))

install_reqs = parse_requirements('requirements.txt', session=uuid.uuid1())
reqs = [str(req.req) for req in install_reqs]

AUTHOR = "Ionata Digital"
AUTHOR_EMAIL = "developers@ionata.com.au"

setup(name="sensetdp",
      version=version,
      description="Sense-T Data Portal v2 client",
      license="MIT",
      author=AUTHOR,
      author_email=AUTHOR_EMAIL,
      maintainer=AUTHOR,
      maintainer_email=AUTHOR_EMAIL,
      url="https://github.com/ionata/senset-data-portal",
      packages=find_packages(where='src', exclude=['tests']),
      package_dir={'': 'src'},
      install_requires=reqs,
      keywords="sense-t api client library",
      classifiers=[
          'Development Status :: 4 - Beta',
          'Topic :: Software Development :: Libraries',
          'License :: OSI Approved :: MIT License',
          'Operating System :: OS Independent',
          'Programming Language :: Python',
          'Programming Language :: Python :: 2',
          'Programming Language :: Python :: 2.7',
          'Programming Language :: Python :: 3',
          'Programming Language :: Python :: 3.4',
      ],
      extras_require = {
	      'pandas-observation-parser': [
	          'pandas >= 0.18.1'
	      ]
	  },
      zip_safe=True)
