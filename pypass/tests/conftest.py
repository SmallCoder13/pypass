def pytest_addoption(parser):
    parser.addoption("--api-key", action="store", help="Github API key")
