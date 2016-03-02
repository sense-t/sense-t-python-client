Sense-T Data Portal v2 client
==============================

This project is a python client implementation for the [Sense-T Data Portal v2 API](https://data.sense-t.org.au/api/sensor/v2/api-docs/#/).

Project home page: https://github.com/ionata/senset-data-portal

Installation
------------

Install from the master branch:

    $ pip install -e git+https://github.com/ionata/senset-data-portal.git#egg=senset-data-portal

Or install from a tag:

    $ pip install -e git+https://github.com/ionata/senset-data-portal.git@v2.0.4#egg=senset-data-portal

Documentation
------------

todo

Roadmap
------------

* Define unimplemented models
* Define unimplemented API endpoints

Development
------------

Clone the project from github:

    $ git clone https://github.com/ionata/senset-data-portal.git
    $ cd senset-data-portal

Create a python virtual environment, then install the requirements as below:

    $ (venv) pip install -r requirements.txt && pip install -r test_requirements.txt

Testing
------------

Run the test suite with:

    $ (venv) nosetests -v tests.test_auth tests.test_api

Or, use `tox` to run the setup.py package build and test suite for all python versions (ensure your environment variables for any API calls that hit the web are correct, see `tox.ini` passenv configuration):

    $ (venv) tox

#### Acknowledgements

This project has been heavy derived from the Tweepy python twitter client project: https://github.com/tweepy/tweepy/ 