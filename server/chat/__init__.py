# initializing logger
from server.commons.logger import initialize
logger = initialize("chat")
if logger is None:
    raise Exception("Failed to initialize 'chatserver' logger.")
