
"""
 This is the data models script 
 it contains the classes of the models to be used for rendereing jinja pages
"""
import server.commons.utils as utils


class Agency(object):
    """
     Class to hold Agency details.
    """
    def __init__(self, _agency):
        self.id = _agency["_id"]
        self.name = _agency["name"].title() if _agency.get("name") else ""
        self.description = _agency["description"].strip() if _agency.get("description") else ""
        self.feed_type = _agency["config"]["type"].upper() if _agency.get("config", {}).get("type") else ""

        self.feed_format = _agency["config"]["data_format"].upper() if _agency.get("config", {}).get("data_format") else ""
        self.url = _agency["config"]["url"] if _agency.get("config", {}).get("url") else ""


class Category(object):
    """
     Class to hold the category details.
    """
    def __init__(self, _category):
        self.id = _category["_id"]
        self.name = _category["name"].title() if _category.get("name") else ""


class Share(object):
    """
     Class to hold the share details.
    """
    def __init__(self, _share):
        self.id = _share["_id"]
        self.name = _share["name"].title() if _share.get("name") else ""
        self.created_time = _share["created_time"].split(" ")[0] if _share.get("created_time", "") else ""
        self.type = _share["type"].strip().capitalize() if _share.get("type") else ""
        self.protocol = _share["protocols"][0].strip().upper() if _share.get("protocols") else ""
        self.state = _share["state"].strip().capitalize() if _share.get("state") else ""


class Story(object):
    """
     Class to store the story details.
     if the complete details are required then populate is called.
    """
    def __init__(self, _story, detailed_info=False):
        self.id = _story["_id"]
        self.title = _story["story_title"] if _story.get("story_title") else ""
        self.reporter_name = _story["user_info"]["display_name"] if _story.get("user_info", {}).get("display_name") else ""
        self.created_datetime = _story.get("created_datetime", "")
        self.incident_date = "{}".format(_story["incident_date"]) if "incident_date" in _story else ""
        self.incident_time = "{}".format(_story["incident_time"]) if "incident_time" in _story else ""
        self.category = _story.get("category_info", {}).get("name", "")
        self.tags = [tag.get("name") for tag in _story.get("tags_info_list")]
        self.description = _story["description"] if "description" in _story else ""
        if detailed_info:
            self.attachments = []
            self.populate(_story)

    def populate(self, _story):
        """
         Populate the remaining keys for the detailed information
        """
        video_url = None
        for attachment in _story.get("attachments"):
            # print("Attachment is: {}".format(attachment))
            _temp = dict()
            _temp["file_name"] = attachment.get("file_name")
            _temp["file_size"] = attachment.get("file_size")

            _temp["type"] = attachment.get("type")
            _temp["created_date"] = attachment.get("created_date")
            _temp["source_url"] = utils.get_media_url(path=attachment.get("path"),
                                                      media_type=_temp["type"])
            self.attachments.append(_temp)
            if not video_url:
                if _temp["type"] == "video":
                    video_url = _temp["source_url"]
        if not video_url and self.attachments:
            video_url = self.attachments[0]["source_url"]
        self.source_url = video_url
        print(self.source_url)
        # print("Story original attachments are  :{}".format(_story.get("attachments")))
        # print("Story attachments are : {}".format(self.attachments))
        # pass 


class Editor(object):
    """
     Class to hold the editor details.
    """
    def __init__(self, _editor):
        """
        The editor (NRCS) details
        """
        self.id = _editor.get("_id")
        self.app_name = _editor["name"]
        self.protocol = _editor["protocol"]
        self.data_format = _editor["data_format"]
        self.ip = _editor.get("credentials", {}).get("ip", '')


class Stream(object):
    """
     Class to hold the stream details.
    """
    def __init__(self, _stream):
        self.name = _stream.get("name")
        self.url = _stream.get("url")
        self.userid = _stream.get("userid")
        self.status = _stream.get("status")
        self.play_url = utils.generate_stream_url(_stream.get("name"))
