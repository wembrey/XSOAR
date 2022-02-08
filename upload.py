#!/usr/bin/env python

#import the modules we need
import requests
import json
import sys
import datetime


#Import the conig file that has the connection details
import config

# Get Global variables from config file
tenant = config.tenant
apikey = config.apikey

#set the URL for the API
host = 'https://' + tenant + '.dev.demisto.live'
endpoint_create = '/indicator/create'
endpoint_search = '/indicators/search'


# check if the indicator exists
def check_indicator(query_value):
    global logfile
    url = host + endpoint_search
    result = 'none'
    tags_list = []
    # set the payload
    querystring = "value:" + str(query_value)

    json_payload = {
        "query": querystring
        }

    payload = json.dumps(json_payload)
    headers = {
      'Content-Type': 'application/json',
      'Authorization': apikey
      }

    try:
        response = requests.request("POST", url, headers=headers, data=payload)
        if len(response.json()['iocObjects']) == 0:
            result = 'clear'
            return result, tags_list
        elif 'CustomFields' not in response.json()['iocObjects'][0]:
            value = response.json()['iocObjects'][0]['value']
            tags_list = []
            logfile+='\n' + value + ' found with no tags: '
            print(f'{query_value}: found with no tags')
            return (value, tags_list)
        else:
            value = response.json()['iocObjects'][0]['value']
            tags_list = response.json()['iocObjects'][0]['CustomFields']['tags']
            logfile+='\n' + value + ' found with tags: ' + str(tags_list)
            print(f'{query_value}: found with tags: {str(tags_list)}')
            return (value, tags_list)
    except Exception as e:
        print(f'\nIndicator checking module Failed with error:\n{e}')
        logfile = logfile + str(e)


# define a function to send the API call
def add_indicator(data_list):
    global logfile
    url = host + endpoint_create
    x = 0
    y = 0
    for entry in data_list:

        #build the payload string for the indicator in json
        indicator_type = entry['type']
        sourcebrands = ["local-database"]
        tag_1 = 'unvalidated'
        tag_2 = 'local-db'
        tag_3 = entry['tag3']
        tag_list = [tag_1, tag_2, tag_3]

        # check if it already exists and get the tags
        try:
            result, current_tags = check_indicator(entry['value'])
            if result == entry['value']:
                tag_list.extend(current_tags)
                tag_set = set(tag_list)
                tag_list = list(tag_set)
                tag_list.sort()
            elif result == 'clear':
                print(f'No entry found for {entry["value"]}')
            elif result != entry['value']:
                my_alert = 'Mismatch alert: ' + str({entry['value']}) \
                + 'returned: ' + str({result})
                logfile = logfile + my_alert
                print(my_alert)
        except Exception as e:
            print(f'\ncheck_indicator failed with error:\n{e}')
            logfile = logfile + str(e)

        customfields = {"tags": tag_list}
        value = entry['value']

        # set the payload
        json_payload = {
            "indicator": {
                "indicator_type": indicator_type,
                "sourceBrands": sourcebrands,
                "CustomFields": customfields,
                "value": value
                }
            }

        payload = json.dumps(json_payload)
        headers = {
          'Content-Type': 'application/json',
          'Authorization': apikey
          }

        try:
            response = requests.request("POST", url, headers=headers, data=payload)
            if (response.ok == True) and (result == entry['value']):
                logfile+='\n' + value + ':' + str(tag_list) + ' - updated'
                y += 1
            elif response.ok == True:
                logfile+='\n' + value + ' - OK'
                x += 1
            else:
                logfile+='\n' + value + ' - Failed'
        except Exception as e:
            print(f'\nAdd Indicator failed with error:\n{e}')
            logfile = logfile + str(e)

    print(f'Finished job: {x} indicators added and {y} updated.')

# define a function to get indicators and load to dictionary
def get_indicators(infile):
    global logfile
    data_list = []
    # Check if zone conversion file was added and load it
    try:
        f = open(infile, 'r')
        indicators = f.read()
        indicator_list = indicators.split('\n')
        print(f'\nindicators imported from file')
        f.close()
    except Exception as e:
        print(f'\nFile open of {infile} failed with error:\n{e}')
        logfile = logfile + str(e)
        sys.exit()

    x = 0
    for indicator in indicator_list:
        x += 1
        if len(indicator) > 0:
            try:
                value, type, tag3 = indicator.split(',')
                data_list.append({"value": value, "type": type, "tag3": tag3})
            except Exception as e:
                print(f'\nMapping failed for "{indicator}" at line {x} with error:\n{e}')
                sys.exit()

    return data_list


# define a function to write a log file
def write_logfile(infile):
    global logfile
    filename = infile + datetime.datetime.now().strftime("log_%d_%m_%Y_%H_%M.log")
    try:
        print(f'Opening {filename}')
        f = open(filename, 'w')
        print(f'Writing data to file')
        f.write(logfile)
        print('Closing\n')
        print(logfile)
        f.close()
    except Exception as e:
        print(f'Operation failed with error:\n{e}')
        error_log = error_log + '\n' + str(e)
        #print(logfile)
        print('\nExiting now')
        sys.exit()


def main():
    global logfile
    args = sys.argv[1:]
    if len(args) < 1:
        print(f'Please specify a filename for import')
        sys.exit()
    for item in args:
        logfile = 'Log File\n'
        data_list = get_indicators(item)
        add_indicator(data_list)
        write_logfile(item)
        print(logfile)


if __name__ == "__main__":
    main()
