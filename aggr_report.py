################################################################################################
#                                                                                                                                                                                                          #
#                                                                    Script to fetch Capacity details from AIQ                                                                       #
#                                                                                                                                                                                                          #
################################################################################################


import getpass
import http.client
import json
import pandas as pd
import openpyxl


def fetch_access_token(error_count):

    try:
        access_token = getpass.getpass(prompt='Access Token: ', stream=None)
        return access_token
    except:
        print("\nRan into an error, Try again \n")
        error_count += 1
        if error_count < 5:
            fetch_access_token(error_count)
        else:
            print("\nMax reties reached, Exiting\n")
            exit


def read_serials():

    try:
        with open("./serials.txt") as f:
            serials = f.read().split('\n')
        return serials
    except:
        print(
            "Unable to fetch Serial numbers from serials.txt. Please check the file exists")


def get_node_info(access_token, serial):

    connection = http.client.HTTPSConnection("api.activeiq.netapp.com")
    headers = {
        'content-type': "application/json",
    }
    headers['authorizationtoken'] = access_token
    api_path = f"/v1/clusterview/get-node-summary/{serial}"
    connection.request(
        "GET", api_path, headers=headers)
    response = connection.getresponse()
    data = response.read()
    json_data = json.loads(data)
    return json_data['data'][0]['hostname']


def get_aggr_info(access_token, serial):

    connection = http.client.HTTPSConnection("api.activeiq.netapp.com")
    headers = {
        'content-type': "application/json",
    }
    headers['authorizationtoken'] = access_token
    api_path = f"/v1/clusterview/get-aggregate-summary/{serial}"
    connection.request(
        "GET", api_path, headers=headers)
    response = connection.getresponse()
    data = response.read()
    json_data = json.loads(data)
    aggr_count = len(json_data['data'])
    data_aggr_count = 0
    aggr_names = []
    total_capacities = []
    used_capacities = []
    available_capacities = []
    percent_used = []
    for i in range(0, aggr_count):
        if 'aggr0' not in json_data['data'][i]['local_tier_name']:
            data_aggr_count += 1
            aggr_names += [json_data['data'][i]['local_tier_name']]
            total_capacities += [str(json_data['data']
                                     [i]['usable_capacity_tib'])]
            used_capacities += [str(json_data['data'][i]['used_capacity_tib'])]
            available_capacities += [str(json_data['data']
                                         [i]['available_capacity_tib'])]
            percent_used += [str(json_data['data'][i]['used_data_percent'])]
    return (data_aggr_count, aggr_names, total_capacities, used_capacities, available_capacities, percent_used)


if __name__ == '__main__':
    error_count = 0
    access_token = fetch_access_token(error_count)
    serials = read_serials()
    data_dict = {"Controller Name/Serial Number": [], "Aggregate Name": [],
                 "Total TiB": [], "Used TiB": [], "Available TiB": [], "Percent Used": []}
    for serial in serials:
        print(serial)
        try:
            node_name = get_node_info(access_token, serial)
            data_aggr_count, aggr_names, total_capacities, used_capacities, available_capacities, percent_used = get_aggr_info(
                access_token, serial)

            for i in range(0, data_aggr_count):

                data_dict['Controller Name/Serial Number'] += [node_name]
                data_dict['Aggregate Name'] += [aggr_names[i]]
                data_dict['Total TiB'] += [total_capacities[i]]
                data_dict['Used TiB'] += [used_capacities[i]]
                data_dict['Available TiB'] += [available_capacities[i]]
                data_dict['Percent Used'] += [percent_used[i]]
        except:
            print(
                f"Error occured for serial: {serial}, Check serial number validity or access token validity.")

    df = pd.DataFrame(data_dict)
    df.to_excel('./report.xlsx', engine='openpyxl')
