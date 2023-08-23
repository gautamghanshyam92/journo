import os
import re
import socket
import datetime
import functools
from collections import namedtuple
import asyncio

import aiofiles.os as aios
import aioftp

import server.commons.constants as consts
from server.commons.logger import logger


def is_valid_prefix_url(url):
    """
    checks whether a given url is having protocol prefix or not. Example 'file://', 'ftp://'
    """
    return re.search(r"^.+://.+$", url) is not None


class AioFilePath:
    """
    This class implements interface to perform os operations on a file path.
    """
    def __init__(self, path):
        self.path = path

    @classmethod
    def from_url(cls, url):
        if not url or "://" in url:
            return None
        return AioFilePath(url)

    async def stat(self):
        return await aios.stat(self.path)

    async def rename(self, dst):
        __rename = getattr(aios, "rename", aios.wrap(os.rename))
        return await __rename(self.path, dst)

    async def remove(self):
        __remove = getattr(aios, "remove", aios.wrap(os.remove))
        return await __remove(self.path)

    async def mkdir(self):
        __mkdir = getattr(aios, "mkdir", aios.wrap(os.mkdir))
        return await __mkdir(self.path)

    async def rmdir(self):
        __rmdir = getattr(aios, "rmdir", aios.wrap(os.rmdir))
        return await __rmdir(self.path)

    async def exists(self):
        __exists = aios.wrap(os.path.exists)
        return await __exists(self.path)

    async def getatime(self):
        __getatime = aios.wrap(os.path.getatime)
        return await __getatime(self.path)

    async def getctime(self):
        __getctime = aios.wrap(os.path.getctime)
        return await __getctime(self.path)

    async def getmtime(self):
        __getmtime = aios.wrap(os.path.getmtime)
        return await __getmtime(self.path)

    async def getsize(self):
        __getsize = aios.wrap(os.path.getsize)
        return await __getsize(self.path)

    async def isdir(self):
        __isdir = aios.wrap(os.path.isdir)
        return await __isdir(self.path)

    async def isfile(self):
        __isfile = aios.wrap(os.path.isfile)
        return await __isfile(self.path)


# Class to handle ftp protocol paths
class AioFtpPath:
    """
    This class implements interface to perform os specific operation on an ftp url
    """
    DEFAULT_FTP_PORT = 21
    FtpPathParams = namedtuple("FtpPathParams", "ip port username password path")

    class SingleSession:
        is_logged_in: bool
        __instance = None

        def __new__(cls, host, port=aioftp.DEFAULT_PORT, user=aioftp.DEFAULT_USER,
                    password=aioftp.DEFAULT_PASSWORD, account=aioftp.DEFAULT_ACCOUNT):
            if AioFtpPath.SingleSession.__instance is None:
                logger.info("[AioFtpPath.SingleSession.__new__]: New instance is created.")
                AioFtpPath.SingleSession.__instance = super(AioFtpPath.SingleSession, cls).__new__(cls)
                AioFtpPath.SingleSession.__instance.client = aioftp.Client()
                AioFtpPath.SingleSession.__instance.host = host
                AioFtpPath.SingleSession.__instance.port = port
                AioFtpPath.SingleSession.__instance.user = user
                AioFtpPath.SingleSession.__instance.password = password
                AioFtpPath.SingleSession.__instance.account = account
                AioFtpPath.SingleSession.__instance.is_logged_in = False
                AioFtpPath.SingleSession.__instance.__lock = asyncio.Lock()
            return AioFtpPath.SingleSession.__instance

        async def __aenter__(self):
            await self.__login()
            return self

        async def __aexit__(self, *exc_info):
            pass

        def __del__(self):
            logger.info("[AioFtpPath.SingleSession]: Object going out of scope.")
            yield from self.logout()

        async def __login(self):
            async with self.__lock:
                if self.is_logged_in:
                    return
                try:
                    await self.client.connect(self.host, self.port)
                    await self.client.login(self.user, self.password, self.account)
                    self.is_logged_in = True
                    logger.info("[AioFtpPath.SingleSession.login]: User '{}@{}' logged in successfully."
                                .format(self.user, self.host))
                except Exception:
                    self.client.close()
                    self.is_logged_in = False
                    raise

        async def logout(self):
            if not self.is_logged_in:
                return
            await self.client.quit()
            self.is_logged_in = False
            logger.info("[AioFtpPath.SingleSession.logout]: User '{}@{}' logged out successfully."
                        .format(self.user, self.host))

        async def safe_call(self, func, *args, **kwargs):
            relogin_required = False
            error = None
            try:
                return await getattr(self.client, func)(*args, **kwargs)
            except aioftp.StatusCodeError as err:
                error = err
                for code in err.received_codes:
                    if code.matches("x2x") and (code.matches("4xx") or code.matches("5xx")):
                        relogin_required = True
                    elif code.matches("x3x") and (code.matches("4xx") or code.matches("5xx")):
                        relogin_required = True
            except (ConnectionResetError, OSError, socket.gaierror) as err:
                error = err
                relogin_required = True
            if relogin_required:
                logger.info("[AioFtpPath.SingleSession.safe_call]: Client ran into error '{}'. "
                            "Retrying login and then executing command '{}' again.".format(error, func))
                self.is_logged_in = False
                await self.__login()
                return await getattr(self.client, func)(*args, **kwargs)
            else:
                raise error

    def __init__(self, host, port, username, password, path,
                 account=aioftp.DEFAULT_ACCOUNT, offset_path=None):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.account = account
        self.path = path
        self.offset_path = offset_path
        self.session = AioFtpPath.SingleSession(self.host, self.port,
                                                self.username, self.password,
                                                self.account)

    @classmethod
    def get_params_from_url(cls, url):
        # removing prefix and splitting url by '@'
        _url_parts = re.split(r"@", url.split(consts.FTP_URI_PREFIX)[-1], 1)
        if len(_url_parts) != 2:
            return None
        # splitting to get username and password
        user_pass = re.split(r":", _url_parts[0], 1)
        if len(user_pass) != 2:
            return None
        # splitting to get ip_port and path
        ip_port_path = re.split(r"/", _url_parts[1], 1)
        if len(ip_port_path) != 2:
            return None
        ip_port_path[1] = "/"+ip_port_path[1]
        # splitting to get ip and port
        ip_port = re.split(r":", ip_port_path[0], 1)
        if len(ip_port) == 2:
            return AioFtpPath.FtpPathParams(ip_port[0], int(ip_port[1]), user_pass[0],
                                            user_pass[1], ip_port_path[1])
        else:
            return AioFtpPath.FtpPathParams(ip_port[0], AioFtpPath.DEFAULT_FTP_PORT, user_pass[0],
                                            user_pass[1], ip_port_path[1])

    @classmethod
    def from_url(cls, url):
        if not url or not url.startswith(consts.FTP_URI_PREFIX):
            raise TypeError("Invalid url provided. Given url is not a ftp url")

        params = AioFtpPath.get_params_from_url(url)
        if params is None:
            raise ValueError("Invalid url provided. Failed to extract url parameters")
        return AioFtpPath(params.ip, params.port, params.username, params.password, params.path)

    async def stat(self):
        async with self.session as session:
            return await session.safe_call("stat", self.path)

    async def rename(self, dst):
        async with self.session as session:
            return await session.safe_call("rename", self.path, dst)

    async def remove(self):
        async with self.session as session:
            return await session.safe_call("remove", self.path)

    async def mkdir(self):
        async with self.session as session:
            return await session.safe_call("make_directory", self.path, False)

    async def rmdir(self):
        async with self.session as session:
            return await session.safe_call("remove_directory", self.path)

    async def exists(self):
        async with self.session as session:
            return await session.safe_call("exists", self.path)

    async def getatime(self):
        return None

    async def getctime(self):
        return None

    async def getmtime(self):
        async with self.session as session:
            st = await session.safe_call("stat", self.path)
            mtime = st.get("modify")
            if mtime:
                return datetime.datetime.strptime(st.get("modify"), '%Y%m%d%H%M%S')\
                    .timestamp()
            return None

    async def getsize(self):
        async with self.session as session:
            st = await session.safe_call("stat", self.path)
            return st.get("size", None)

    async def isdir(self):
        async with self.session as session:
            return await session.safe_call("is_dir", self.path)

    async def isfile(self):
        async with self.session as session:
            return await session.safe_call("is_file", self.path)


class AioFsPath:
    """
    Adapter class to provide single interface to manage all operations on a path for different file sharing protocols.
    """
    # mapping between path prefix and responsible handle class
    PATH_HANDLERS = {
        consts.FTP_URI_PREFIX: AioFtpPath.from_url,
        consts.FILE_URI_PREFIX: AioFilePath.from_url
    }

    async def __method_not_implemented(self, method_name):
        if self.path_handler is not None and hasattr(self.path_handler, "__class__"):
            raise NotImplementedError("Method '{}' not implemented for '{}'."
                                      .format(method_name, self.path_handler.__class__))
        else:
            raise NotImplementedError("Method '{}' not implemented.".format(method_name))

    def __init__(self, url):
        self.url = url
        self.path_handler = None
        # looking for suitable handler from registered path handlers for given url
        _url = re.split(r"://", url, 1)
        if is_valid_prefix_url(url):
            self.path_handler = AioFsPath.PATH_HANDLERS.get(_url[0] + "://", lambda x: None)(url)
        else:
            self.path_handler = AioFilePath.from_url(url)

        # validating if suitable handler is found.
        if self.path_handler is None:
            raise ModuleNotFoundError("No suitable module found to handle given url with '{}' protocol"
                                      .format(_url[0]))

    async def stat(self):
        return await getattr(self.path_handler, "stat",
                             functools.partial(self.__method_not_implemented, "stat"))()

    async def rename(self, dst):
        return await getattr(self.path_handler, "rename",
                             functools.partial(self.__method_not_implemented, "rename"))(dst)

    async def remove(self):
        return await getattr(self.path_handler, "rename",
                             functools.partial(self.__method_not_implemented, "remove"))()

    async def mkdir(self):
        return await getattr(self.path_handler, "mkdir",
                             functools.partial(self.__method_not_implemented, "mkdir"))()

    async def rmdir(self):
        return await getattr(self.path_handler, "rmdir",
                             functools.partial(self.__method_not_implemented, "rmdir"))()

    async def exists(self):
        return await getattr(self.path_handler, "exists",
                             functools.partial(self.__method_not_implemented, "exists"))()

    async def getatime(self):
        return await getattr(self.path_handler, "getatime",
                             functools.partial(self.__method_not_implemented, "getatime"))()

    async def getctime(self):
        return await getattr(self.path_handler, "getctime",
                             functools.partial(self.__method_not_implemented, "getctime"))()

    async def getmtime(self):
        return await getattr(self.path_handler, "getmtime",
                             functools.partial(self.__method_not_implemented, "getmtime"))()

    async def getsize(self):
        return await getattr(self.path_handler, "getsize",
                             functools.partial(self.__method_not_implemented, "getsize"))()

    async def isdir(self):
        return await getattr(self.path_handler, "isdir",
                             functools.partial(self.__method_not_implemented, "isdir"))()

    async def isfile(self):
        return await getattr(self.path_handler, "isfile",
                             functools.partial(self.__method_not_implemented, "isfile"))()
