#!/usr/bin/python
# To provide an command line interface to Journo
#       Categories (View, Create, Update, Delete)
#       Tags        (View, Create, Update, Delete)
#       Shares      (View, Create, Update, Delete)
#       agencies    (View, Create, Update, Delete)
#
import argparse
import asyncio
import aiohttp
import json
import sys
# import commons.utils as utils


def print_tabular(data_list, fields):
    tabular_content = []
    header_str = ["{0: ^20}".format(item) for item in fields ]
    tabular_content.append(" | ".join(header_str))
    for item in data_list:
        tmp_str = ''
        for k in fields:
            tmp_str += '{0:^20} | '.format(str(item.get(k)))
        tabular_content.append(tmp_str)
    print('\n\n')
    print('_'*80)
    for row in tabular_content:
        print(row)
    print('_'*80)
    print('\n\n')


def setup_parser():
    """
     Setup the arguments for the parser.
    """
    parser = argparse.ArgumentParser(description="Journo Command Line Interface")
    parser.add_argument("-c", "--categories",
                        help="Categories listing, creating, update & removal.",
                        nargs="+")
    parser.add_argument("-t", "--tags",
                        help="Tags listing, creating, update & removal.",
                        nargs="+")
    parser.add_argument("-s", "--shares",
                        help="Shares listing, creating, update & removal.",
                        nargs="+")
    parser.add_argument("-a", "--agencies",
                        help="Agencies listing, creating, update & removal.",
                        nargs="+")
    return parser


def parse_arguments(args):
    """
    parse the arguments and return the parameters and the current choice.
    :param args: args string the user entered
    :return: the parameters & the choice.
    """
    parameters = []
    choice = ''
    if args.categories:
        parameters = args.categories
        choice = 'categories'
    elif args.tags:
        parameters = args.tags
        choice = 'tags'
    elif args.shares:
        parameters = args.shares
        choice = 'shares'
    elif args.agencies:
        parameters = args.agencies
        choice = 'agencies'
    return parameters, choice


async def view_data(client, choice):
    """
     For all the user choices, calls the get method
    :param client: the async client connection
    :param choice: user choice ssuch as categories, tags, shares, agencies
    :return:
    """
    # async with client.get(utils.get_request_server_url('categories')) as response:
    async with client.get('http://192.168.1.10:7799/{}'.format(choice)) as response:
        assert response.status == 200
        return json.loads(await response.read())


def prepare_data(choice, details):
    """
    For a given choice , prepare the data structure to be posted.
    :param choice: categories, tags, agencies, shares etc
    :param details : data related to new_entry or update info
    :return: the structured json data
    """
    if choice == 'categories':
        return json.dumps({'name': details})
    elif choice == 'tags':
        return json.dumps({'name': details})
    elif choice == 'shares':
        # assume that user pastes json dump data here
        details = details.replace("\'", '\"')
        share_data = json.loads(details)
        return json.dumps(share_data)
    elif choice == 'agencies':
        details = details.replace("\'", '\"')
        agency_data = json.loads(details)
        return json.dumps(agency_data)


async def post_data(client, choice, parameters):
    """
     Post Create Data for the choice
    :param client: post to the client
    :param choice: to create a entry into a choice
    :param parameters: parameters in the create data
    """
    # async with client.get(utils.get_request_server_url('categories')) as response:
    data = prepare_data(choice, parameters[1])
    async with client.post('http://localhost:7799/{}'.format(choice), data=data) as response:
        assert response.status == 200
        return json.loads(await response.read())


async def update_data(client, choice, parameters):
    """
    Update method for the user choice
    :param client: post to the client
    :param choice: to create a entry into a choice
    :param parameters: contains the update id followed by the update data
    """
    # async with client.get(utils.get_request_server_url('categories')) as response:
    data = prepare_data(choice, parameters[2])
    async with client.put('http://localhost:7799/{}/{}'.format(choice, parameters[1]), data=data) as response:
        assert response.status == 200
        return json.loads(await response.read())


async def delete_data(client, choice, parameters):
    """
    Delete method for the user choice.
    :param client: post to the client
    :param choice: to create a entry into a choice
    :param parameters: the entry id to be deleted
    """
    # async with client.get(utils.get_request_server_url('categories')) as response:
    async with client.delete('http://localhost:7799/categories/{}'.format(choice, parameters[1])) as response:
        assert response.status == 200
        return json.loads(await response.read())


async def request_loop(parser, args, loop):
    """
    :param parser: Parser object to parse input
    :param args: current user choices
    :param loop: async loop
    :return:  None
    """
    # TODO : To add while True

    parameters, choice = parse_arguments(args)
    if not parameters and not choice:
        print('\nPlease use help to see valid cli options. \n python {} --help'.format(sys.argv[0]))
        return
    async with aiohttp.ClientSession(loop=loop) as client:
        while True:
            if 'view' == parameters[0]:
                data = await view_data(client, choice)
                keys = list(data[choice][0].keys())
                print_tabular(data[choice], keys)
            elif 'create' == parameters[0]:
                print('Create result is : {}'.format(await post_data(client, choice, parameters)))
            elif 'update' == parameters[0]:
                print('Update result is : {}'.format(await update_data(client, choice, parameters)))
            elif 'delete' == parameters[0]:
                print('Update result is : {}'.format(await delete_data(client, parameters)))
            parameters = display_options(choice, parser)
            if not parameters:
                print('\n Did not receive any new input. Terminating!!')
                break


def display_options(choice, parser):
    """
     Get the user input by depending on the choices.
        :param choice: Choice the user made, such as 'categories', 'tags', 'shares', 'agencies'
        :param parser: parser object to parse the options the user enters
        :return: Parameters after parsing, a list
    """
    # print('\t\t Options for {} '.format(choice))
    arg_string = '--{} '.format(choice) + str(input('journo cli :> --{} '.format(choice)))
    parameters, _ = parse_arguments(parser.parse_args(arg_string.split()))
    return parameters


if __name__ == "__main__":
    parser = setup_parser()
    args = parser.parse_args()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(request_loop(parser, args, loop))
