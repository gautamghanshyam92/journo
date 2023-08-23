import json

import aiohttp.web as aioweb
import aiohttp_jinja2

from configparser import ConfigParser
# importing logger
from server.request import logger
import server.commons.utils as utils
from server.commons import session
from server.request.models import Agency,Category,Share,Story,Editor,Stream

routes = aioweb.RouteTableDef()

"""
The responsibility of this module is to render pages to the web
/pages : to render jinja templates
/web : to render static pages
"""


def get_static_routes():
    return [aioweb.static("/pages", "web"), 
            aioweb.static("/web", 'web')]


async def prepare_shares_edit_context(context):
    """
    Preparing the share context
    :param context:
    :return: new context of shares
    """
    shares_edit_context = []
    if context and context.get('shares'):
        shares_edit_context = [ Share(_share) for _share in context["shares"]]
    return shares_edit_context


async def prepare_editors_edit_context(context):
    """
     Prepare the editors context (NRCS)
     :param context:
     :return: new context of editors
    """
    editors_context = []
    if context and context.get("nrcs"):
        editors_context = [Editor(_editor) for _editor in context['nrcs']]
    return editors_context


async def prepare_categories_edit_context(context):
    """
    Preparing the categories context
    :param context: data that will be filled into the jinja template
    :return: modified context to match the page
    """
    categories_edit_context = []
    if context and context.get('categories'):
        categories_edit_context = [Category(_category=cat) for cat in context["categories"]]
    return categories_edit_context


async def prepare_agencies_edit_context(context):
    """
    Preparing the agencies edit context
    :param context: Data that will be filled into the jinja template
    :return: modified context to match the fields on the page
    """
    agencies_edit_context = []
    if context and context.get("agencies"):
        agencies_edit_context = [Agency(_agency=_agency) for _agency in context["agencies"]]
    return agencies_edit_context


async def prepare_story_feed_context(context):
    """
     Prepare the data for the  story feed
    :param context: data that will be used to fill the jinja template
    :return: modified context that will be used to match the fields on the page
    """
    stroy_feed_context = []
    if context and context.get("stories"):
        stroy_feed_context = [Story(_story) for _story in context["stories"]]
    return stroy_feed_context


async def prepare_story_detail_context(context):
    """
     Populate the data into the data structure required by Jinja Page
     Story Detail context
    """
    story_context = {}
    if context and context.get("story"):
        story_context = Story(context["story"], detailed_info=True)
    return story_context


async def prepare_stream_context(context):
    """
     Populate the data into the data structure required by Jinja Page
     Streams context
    """
    stream_context = {}
    if context and context.get("stream"):
        stream_context = Stream(context["stream"])
    return stream_context


async def handler(request, view, context):
    """
     This module will take in the request object, view and the context object
      Request object to return the web response to the caller (WEB)
      View the view the context needs to be applied to : Such as (Shares, Agencies, Stories, NRCS)
           : type  string, "shares"
      context : Contains the data required to be filled into the jinja template
              : type : dict  having the requested data
    """
    template_mapping = utils.get_template_mapping()
    # logger.info("handler received ; {} \n template is : {}".format(context, template_mapping))
    logger.info("[handler] Serving template for view --> {} -- {}".format(view, template_mapping.get(view)))
    new_context = []
    template_name = None

    if view == "shares":
        # shares view creation
        template_name = template_mapping.get('shares')
        new_context = dict()
        new_context["shares"] = await prepare_shares_edit_context(context)
        pass

    elif view == "categories":
        # categories view creation
        template_name = template_mapping.get("categories")
        new_context = dict()
        new_context["categories"] = await prepare_categories_edit_context(context)
        pass

    elif view == "agencies":
        # agencies view creation
        template_name = template_mapping.get("agencies")
        new_context = dict()
        new_context["agencies"] = await  prepare_agencies_edit_context(context)

    elif view == "storyfeed":
        # stories view creation
        template_name = template_mapping.get("storyfeed")
        new_context = await  prepare_story_feed_context(context)
        pass

    elif view == "index":
        template_name = template_mapping.get("index")
        new_context = dict()
        new_context["agencies"] = await prepare_agencies_edit_context(context["agencies"])
        new_context["storyfeed"] = await prepare_story_feed_context(context['stories'])

    elif view == "settings":
        template_name = template_mapping.get("settings")
        new_context = dict()
        new_context["agencies"] = await prepare_agencies_edit_context(context["agencies"])
        new_context["shares"] = await prepare_shares_edit_context(context["shares"])
        new_context["categories"] = await prepare_categories_edit_context(context["categories"])
        new_context["editors"] = await prepare_editors_edit_context(context['editors'])

    elif view == "story-detail":
        template_name = template_mapping.get("story-detail")
        new_context = dict()
        new_context["agencies"] = await prepare_agencies_edit_context(context["agencies"])
        new_context["story"] = await prepare_story_detail_context(context)

    elif view == "golive":
        template_name = template_mapping.get("golive")
        new_context = dict()
        new_context["stream"] = await prepare_stream_context(context)
        new_context["all_streams"] = await fetch_all_streams()

    if not template_name:
        # TODO 404 not found must be raised
        pass
    logger.info("[handler] Prepared context to be rendered  : {}".format(new_context))

    return aiohttp_jinja2.render_template(template_name,
                                              request,
                                              context={"items": new_context})


async def fetch_shares():
    """
     Function to fetch the shares and return data
    """
    url = utils.get_request_server_url("shares")
    shares_resp = await session.get(url)
    return await shares_resp.json() if shares_resp.status is 200 else None


async def fetch_agencies():
    """
     Function to fetch the agencies and return data
    """
    url = utils.get_request_server_url("agencies")
    agency_resp = await session.get(url)
    return await agency_resp.json() if agency_resp.status is 200 else None


async def fetch_categories():
    """
     Function to fetch the categories and return data
    """
    url = utils.get_request_server_url("categories")
    category_resp = await session.get(url)
    return {"categories" : await category_resp.json()} if category_resp.status == 200 else None


async def fetch_stories(story_id=None, agency_id=None):
    """
    Fetch the stories adn return the data
    :return: story response data 
    """
    if story_id:
        url = utils.get_request_server_url("stories/{}".format(story_id))
        story_resp = await session.get(url)

    elif agency_id:
        url = utils.get_request_server_url("stories?agency_id={}".format(agency_id))
        story_resp = await session.get(url)

    else:
        url = utils.get_request_server_url("stories")
        story_resp = await session.get(url)

    return await story_resp.json() if story_resp.status == 200 else None


async def fetch_editors():
    """
     Function to fetch the editors and return data
    """
    url = utils.get_request_server_url("nrcs")

    editor_resp = await session.get(url)
    return await editor_resp.json() if editor_resp.status == 200 else None


async def fetch_stream(stream_name=None):
    """
     Function to fetch the stream 
    """
    url = utils.get_request_server_url("streams")
    streams_resp = await session.get(url)
    res = await streams_resp.json() if streams_resp.status == 200 else  []
    res.sort(key=lambda k: k["name"])
    if stream_name:
        for stream in res:
            if stream.get("name") == stream_name:
                res = stream
                break
    elif res:
        res = res[0]
    else:
        res = None
    return res

async def fetch_all_streams():
    """
     Function to fetch all the streams 
    """
    url = utils.get_request_server_url("streams")
    streams_resp = await session.get(url)
    res = await streams_resp.json() if streams_resp.status == 200 else  []
    res.sort(key=lambda k: k["name"])
    all_streams = [stream for stream in res]
    return all_streams



@routes.get("/pages/shares")
async def render_shares(request):
    """
     The api that the web calls in order to get the shares page rendered
    """
    # first we get the shares by calling the api
    shares = await fetch_shares()
    logger.info("render_shares : Shares result is : {}".format(shares))
    # Once we hae the data, we send it to handler to render the response
    return await handler(request, "shares", context=shares)


@routes.get("/pages/categories")
async def render_categories(request):
    """
     The api that the web calls in order to get the categories page rendered
    """
    # first we get the categories by calling the api
    categories = await fetch_categories()
    logger.info("render_categories : categories result is : {}".format(categories))
    # Once we have the data, we send it to handler to render the response
    return await handler(request, "categories", context=categories)


@routes.get("/pages/agencies")
async def render_agencies(request):
    """
     The api that the web calls in order to get the agencies page rendered
    """
    # first we get the agencies by calling the api
    agencies = await fetch_agencies()
    logger.info("render_agencies : agencies result is : {}".format(agencies))
    # Once we have the data, we send it to handler to render the response
    return await handler(request, "agencies", context=agencies)


@routes.get("/pages/storyfeed")
async def render_stories(request):
    """
    The api that the web calls in order to get the stories page rendered.
    :param request:
    :return: jinja template rendered
    """
    # first we get the stores by calling the api
    stories = await fetch_stories()
    # logger.info("render_stories: stories response is : {}".format(stories))
    return await handler(request, "storyfeed", context=stories)


@routes.get("/pages/index")
async def render_index(request):
    """
    The api called to render the index page.
    :param request:
    :return: jinja template rendered
    """
    # search keys to filter result
    if request.rel_url.query.get("search"):
        search_filter = json.loads(request.rel_url.query["search"])
    else:
        search_filter = request.rel_url.query

    agency_id = search_filter.get("agency_id")
    agencies = await fetch_agencies()
    if agency_id:
        stories = await fetch_stories(agency_id=agency_id)
    else:
        stories = await fetch_stories()

    context = {"agencies": agencies, "stories": stories}
    return await handler(request, "index", context)


@routes.get("/pages/settings")
async def render_settings(request):
    """
    The api called to render the settings page.
    :param request:
    :return: jinja template rendered
    """
    agencies = await fetch_agencies()
    shares = await fetch_shares()
    categories = await fetch_categories()
    editors = await fetch_editors()
    context = {"agencies": agencies, "shares": shares,
                "categories": categories, "editors": editors}
    return await handler(request, "settings", context)


@routes.get("/pages/story/{story_id}")
async def render_story_detail(request):
    """
     The api to render the story detail page.
     :param request:
     :return jinja template rendered
    """
    story_id = request.match_info["story_id"]
    story = await fetch_stories(story_id)
    agencies = await fetch_agencies()
    context = {"story": story, "agencies": agencies}
    return await handler(request, "story-detail", context)


@routes.get("/pages/golive")
async def render_streams(request):
    """
    The api called to render the golive page.
    :param request:
    :return: jinja template rendered
    """
    search_filter = request.rel_url.query
    stream_name = search_filter.get("stream_name")
    stream = await fetch_stream(stream_name)
    context = {"stream": stream}
    return await handler(request, "golive", context)

