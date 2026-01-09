import pytest


#@pytest.fixture
#def get_api_key(config):
#    return config.getoption("--api-key"

def pytest_addoption(parser):
    parser.addoption("--api-key", action="store", help="Github API key") 
