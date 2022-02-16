#!/usr/bin/env python

#import the modules we need
import requests
import json
import sys
import datetime

colors = {
        'blue': '\033[94m',
        'pink': '\033[95m',
        'green': '\033[92m',
        'red': '\033[91m', #red
        'yellow': '\033[93m', #yellow
        }

def highlight(string, color):
    if not color in colors: return string
    return colors[color] + string + '\033[0m'

#Import the conig file that has the connection details
import config

# Get Global variables from config file
tenant = config.tenant
apikey = config.apikey

#set the URL for the API
host = 'https://' + tenant + '.dev.demisto.live'
endpoint_create = '/indicator/create'
endpoint_search = '/indicators/search'
endpoint_edit = '/indicator/edit'

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
        #Check if more than one item is returned and get correct one
        if len(response.json()['iocObjects']) > 1:
            for item in response.json()['iocObjects']:
                if item['value']!= query_value:
                    pass
                elif item['value'] == query_value:
                    iocobject = item
        #if none returned - it's clear
        elif len(response.json()['iocObjects']) == 0:
            result = 'clear'
            return result, tags_list

        elif len(response.json()['iocObjects']) == 1:
            iocobject = response.json()['iocObjects'][0]

        if 'CustomFields' not in iocobject:
            value = iocobject['value']
            iocobject['CustomFields'] = {'tags': []}
            logfile+='\n' + value + ' found but with no tags: '
            print(f'{query_value}: found with no tags')
            return (value, iocobject)
        elif 'tags' not in iocobject['CustomFields']:
            value = iocobject['value']
            iocobject['CustomFields'] = {'tags': []}
            logfile+='\n' + value + ' found but with no tags: '
            print(f'{query_value}: found with no tags')
            return (value, iocobject)
        else:
            value = iocobject['value']
            tags_list = iocobject['CustomFields']['tags']
            logfile+='\n' + value + ' found with tags: ' + str(tags_list)
            print(f'{query_value}: found with tags: {str(tags_list)}')
            return (value, iocobject)
    except Exception as e:
        print(f'\nIndicator checking module Failed with error:\n{e}')
        logfile = logfile + str(e)


def add_indicator(url, payload, headers, value):
    global logfile
    try:
        response = requests.request("POST", url, headers=headers, data=payload)
        if response.ok == True:
            value = response.json()['value']
            logfile+='\n' + value + ' - OK'
        else:
            logfile+='\n' + value + ' - Failed'
    except Exception as e:
        print(f'\nAdd Indicator failed with error:\n{e}')
        logfile = logfile + str(e)


def update_indicator(url, payload, headers, tag_set):
    #print(f'URL: {url}\nPayload:{payload}\nHeaders:{headers}\nTags:{tag_set}')
    global logfile
    try:
        response = requests.request("POST", url, headers=headers, data=payload)
        if (response.ok == True):
            #print(json.dumps(response.json(), indent=4))
            value = response.json()['value']
            logfile+='\n' + value + ':' + str(tag_set) + ' - updated'
        else:
            logfile+='\n' + value + ' - Failed'
    except Exception as e:
        print(f'\nUpdate Indicator failed with error:\n{e}')
        logfile = logfile + str(e)

# define a function to send the API call
def process_indicator(data_list):
    global logfile
    x = 0
    y = 0
    for entry in data_list:

        #build the payload string for the indicator in json
        indicator_type = entry['type']
        sourcebrands = ["local-database"]
        tag_1 = 'unvalidated'
        tag_2 = 'local-db'
        tags = entry['tags']
        tag_list = [tag_1, tag_2]
        tag_list.extend(tags)

        # check if it already exists and get the tags
        try:
            result, iocobject = check_indicator(entry['value'])
            if result == entry['value']:
                iocobject['CustomFields']['tags'].extend(tag_list)
                tag_set = set(iocobject['CustomFields']['tags'])
                iocobject['CustomFields']['tags'] = list(tag_set)
                iocobject['CustomFields']['tags'].sort()

                # send the result for updating tags
                url = host + endpoint_edit
                payload = json.dumps(iocobject)
                headers = {
                  'Content-Type': 'application/json',
                  'Authorization': apikey
                  }
                update_indicator(url, payload, headers, tag_set)
                y += 1

            elif result == 'clear':
                print(f'No entry found for {entry["value"]}')

                # set the payload
                url = host + endpoint_create
                customfields = {"tags": tag_list}
                value = entry['value']
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

                add_indicator(url, payload, headers, value)
                x += 1
        except Exception as e:
            print(f'\nprocess_indicator failed with error:\n{e}')
            logfile = logfile + str(e)

    logstring = f'\n\nFinished job: {highlight(str(x),"red")}' \
        f' {highlight("indicators added","red")}' \
        f'  and {highlight(str(y) + " updated","yellow")} .'
    print(logstring)
    logfile = logfile + logstring

# define a function to get indicators and load to dictionary
def get_indicators(infile):
    global logfile
    data_list = []
    input_list = []
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
                input_list = indicator.split(',')
                value, type, = input_list[0], input_list[1]
                tags = input_list[2:]
                data_list.append({"value": value, "type": type, "tags": tags})
                #print(f'Data list: {data_list}')
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
        print(logfile)
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
        process_indicator(data_list)
        write_logfile(item)
        #print(logfile)


if __name__ == "__main__":
    main()
