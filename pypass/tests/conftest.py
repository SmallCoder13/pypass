def pytest_addoption(parser):
    parser.addoption("--api-key", action="store", help="Github API key") 
    parser.addoption("--target", required=False, help="Target platform for test suite (do not pass, only there so tests don't fail in github CI)")
