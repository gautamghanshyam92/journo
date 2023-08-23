# initializing logger
from server.commons.logger import initialize
logger = initialize("request")
if logger is None:
    raise Exception("Failed to initialize 'RequestServer' logger.")