#
# Steps to upload a story along with files.
#

# STAGE-1
'''
Description: Create new story
Request: "/stories" POST
{
	"story_title": "Balakot Strike Confirmation",
	"category_id": "88abc73186dd4ba0ba8e972502605847",
	"description": "Italian reporter confirms that 170 terrorists were killed in Balakot Air Strike",
	"tags": ["32a6f82d999648df922e6486ee3d280c"],
	"attachments": ["filename_1.mov", "filename_2.mov"],
	"user_id": "44bcb9a74929413b9e2cb196c77f3f45",
	"incident_date": "2019-02-08",
	"incident_time": "22:08:59"
}

Response:
{
    "story_id": "9a1d7bbada335a98c2de3511cb93b3ff",
    "attachments": [
        {
            "asset_id": "9a1d7bbada335a98c2de3511cb93b3ff_file.avi",
            "file_name": "file.avi",
            "state": "pending"
        }
    ],
    "ok": True
}
'''

# STAGE-2
'''
Description: Get the ftp server credentials and location to upload
Request: "/stories-shares" GET
Response:
{
    "share_credentials": {
        "_id": "newsftpstore",
        "ip": "192.168.0.105",
        "name": "News Store",
        "password": "nspaceai",
        "path": "/nstore/uploads",
        "port": 21,
        "protocol": "ftp",
        "rules": {},
        "state": "active",
        "type": "fileshare",
        "username": "nspaceai"
    },
    "destination_folder": "/nstore/uploads/mediastore"
}
'''

# STAGE-3
'''
Description: Create new upload task so that server can track it
Request: "/tasks" POST
{
	"task_name": "upload",
    "story_id": "9a1d7bbada335a98c2de3511cb93b3ff",
    "file_name": "file.avi",
    "file_size": 1234567890,
    "asset_id": "9a1d7bbada335a98c2de3511cb93b3ff_file.avi",
    "dst_path": "share://newsftpstore/mediastore/9a1d7bbada335a98c2de3511cb93b3ff_file.avi"
}

Response:
{
    "task_id": "1243570c1aa1084126168d9ae9184cc49abe76798",
    "story_id": "9a1d7bbada335a98c2de3511cb93b3ff",
    "asset_id": "9a1d7bbada335a98c2de3511cb93b3ff_file.avi"
}
'''

# STAGE-4
'''
Description: FTP-CLIENT connects to FTP Server and starts uploading file and sends progress to Journo Server
Request: "/tasks" PUT
{
	"task_name": "upload",
	"status": "INPROGRESS",
	"bandwidth": 234156,
	"progress": 26.09,
	"task_id": "1243570c1aa1084126168d9ae9184cc49abe76798",
	"story_id": "9a1d7bbada335a98c2de3511cb93b3ff"
}
Response:
{
    "ok": true
}
'''

# STAGE-5
'''
Description: Asset upload verfication and addition to story
Request: "/stories-assets" POST
{
	"story_id": "9a1d7bbada335a98c2de3511cb93b3ff",
	"asset_id": "9a1d7bbada335a98c2de3511cb93b3ff_file.avi",
	"share_id": "newsftpstore",
	"path": "share://newsftpstore/mediastore/9a1d7bbada335a98c2de3511cb93b3ff_file.avi",
	"file_name": "file.avi",
	"file_size": 1234567890
}
'''
