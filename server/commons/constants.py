# Database constants
DB_NAME = "journo"
# Journo agency id
JOURNO_AGENCY_ID = "journofeed"
# Allowed news feed types
FEED_TYPE_RSS = "rss"
FEED_TYPE_REST_GET = "rest-get"
# Data formats supported for news feeds
FEED_DATA_FORMAT_XML = "xml"
FEED_DATA_FORMAT_JSON = "json"

# Date and time formats
DATE_FORMAT = "%Y-%m-%d"
TIME_FORMAT = "%H:%M:%S"
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S.%f"

# Different states to track task
STATE_NEW           = "NEW"
STATE_SCHEDULED     = "SCHEDULED"
STATE_QUEUED        = "QUEUED"
STATE_INITIALIZING  = "INITIALIZING"
STATE_IN_PROGRESS   = "INPROGRESS"
STATE_COMPLETED     = "COMPLETED"
STATE_VERIFYING     = "VERIFYING"
STATE_FAILED        = "FAILED"
STATE_ABORTED       = "ABORTED"

# Application encoding
APP_ENCODING = "utf-8"

# Task Names
TASK_UPLOAD   = "upload"
TASK_DOWNLOAD = "download"
TASK_GENERATE_LOWRES = "generate_lowres"
TASK_GENERATE_THUMBNAIL = "generate_thumbnail"

# Protocols
PROTOCOL_FTP = "ftp"
PROTOCOL_SMB = "smb"
PROTOCOL_FILE = "file"
PROTOCOL_HTTP = "http"
PROTOCOL_TUS = "tus"

# URI Prefixes
SHARE_URI_PREFIX = "share://"
# File sharing protocol prefixes
FTP_URI_PREFIX = "ftp://"
FILE_URI_PREFIX = "file://"
HTTP_URI_PREFIX = "http://"
HTTPS_URI_PREFIX = "https://"
SMB_URI_PREFIX = "smb://"
NFS_URI_PREFIX = "nfs://"

# Share types
SHARE_TYPE_FILE = "fileshare"
SHARE_TYPE_PROXY = "proxyshare"
# Share states
STATE_ACTIVE = "active"
STATE_DISABLED = "disabled"

# File states
FILE_STATE_PENDING = "pending"
FILE_STATE_UPLOADING = "uploading"
FILE_STATE_READY = "ready"

# Format of asset_id
ASSET_ID_FORMAT = "{story_id}__{filename}"

# Stories Proxy Config
STORY_THUMBNAIL_EXTENSION = "jpg"
STORY_LOWRES_EXTENSION = "mp4"
VERSIONS_PER_PAGE = 100
VERSION_TIME_FORMAT = "%Y-%m-%d %H:%M:%S.%f"
VERSIONING_KEYS = ["user_id", "story_title", "description"]

#Template related config
TEMPLATE_BASE_FOLDER = "./web/templates"

# NGINX Config
NGINX_PROXY_ROUTE = "proxy"
NGINX_SOURCE_ROUTE = "media"
NGINX_VIDEO_ROUTE = "play"
NGINX_IMAGE_ROUTE = "view"
NGINX_STREAM_PROTOCOL = "rtmp"
NGINX_CONF_PATH = "/usr/local/nginx/conf/nginx.conf"

STREAM_NAMES_JSON = './settings/streams.json'
STREAM_TIMESTAMP_FORMAT = "%Y-%m-%d %H:%M:%S"
