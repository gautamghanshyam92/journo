# initializing logger
from server.commons.logger import initialize
logger = initialize("task")
if logger is None:
    raise Exception("Failed to initialize 'taskserver' logger.")
