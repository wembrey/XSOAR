#!/usr/bin/env python
version = '1.1'
#import the modules we need
import requests
import json
import sys
import datetime
import os

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

#os.system('clear')
#print(f'Manage.py upload script version: {version}')

#Import the conig file that has the connection details
import config

# Get Global variables from config file
tenant = config.tenant
apikey = config.apikey

#set the URL for the API
host = 'https://' + tenant + '.demisto.live'
endpoint_create = '/indicator/create'
endpoint_search = '/indicators/search'
endpoint_edit = '/indicator/edit'

# check if the indicator exists
def check_indicator(query_value):
    global logfile
    url = host + endpoint_search
    result = 'none'
    tags_list = []
    # deal with tilde "~" in the URL
    if '~' in query_value:
        querystring = query_value[0:query_value.find('~')] + '*'
        #print(f'Q is now: {querystring}')
    else:
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
            print(f'more than one match found for {query_value}')
            matched = False
            iocObjects = response.json()['iocObjects']
            #print(f'\n\n{len(iocObjects)} items matched\n\n')
            # Look for a match for query_value in the returned objects
            for item in response.json()['iocObjects']:
                if item['value']!= query_value:
                    pass
                elif item['value'] == query_value:
                    matched = True
                    iocobject = item
                    value = iocobject['value']
            # If none of them matches
            if not matched:
                result = 'clear'
                return result, tags_list
        #if none returned - it's clear
        elif len(response.json()['iocObjects']) == 0:
            print(f'no results returned for {query_value}')
            result = 'clear'
            return result, tags_list

        elif len(response.json()['iocObjects']) == 1:
            print(f'one match returned for {query_value}')
            iocobject = response.json()['iocObjects'][0]
            value = iocobject['value']
            if iocobject['value'] != query_value:
                #print(f'Wrong value returned for {query_value} vs {value}')
                result = 'clear'
                return result, tags_list

        if 'CustomFields' not in iocobject:
            iocobject['CustomFields'] = {'tags': []}
            logfile+='\n' + value + ' found but with no tags: '
            #print(f'{query_value}: found with no tags')
            return (value, iocobject)
        elif 'tags' not in iocobject['CustomFields']:
            iocobject['CustomFields'] = {'tags': []}
            logfile+='\n' + value + ' found but with no tags: '
            #print(f'{query_value}: found with no tags')
            return (value, iocobject)
        else:
            tags_list = iocobject['CustomFields']['tags']
            logfile+='\n' + value + ' found with tags: ' + str(tags_list)
            #print(f'{query_value}: found with tags: {str(tags_list)}')
            return (value, iocobject)
    except Exception as e:
        print(f'\nIndicator check error for: {query_value}:\n{e}')
        logfile = logfile + '\n\nIndicator checking Error with: ' + \
        query_value + ':' + str(e) + '\n\n'


def add_indicator(url, payload, headers, value):
    global logfile
    try:
        response = requests.request("POST", url, headers=headers, data=payload)
        '''
        if response.ok == True:
            value = response.json()['value']
            logfile+='\n' + value + ' - OK'
        else:
            logfile+='\n' + value + ' - Failed'
            '''
    except Exception as e:
        print(f'\nAdd Indicator failed with error:\n{e}')
        logfile = logfile + '\n\nadd_indicator failed for ' + \
            value + ': ' + str(e) + '\n\n'


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
        logfile = logfile + '\n\nupdate_indicator failed for ' + \
            str(payload) + ': ' + str(e) + '\n\n'

# define a function to send the API call
def process_indicator(data_list, infile):
    errors = 0
    global logfile
    x = 0
    y = 0
    for entry in data_list:

        #build the payload string for the indicator in json
        indicator_type = entry['type']
        if indicator_type == 'ip':
            indicator_type = 'IP'
        sourcebrands = ["local-database"]
        tag_1 = 'unvalidated'
        tag_2 = 'local-db'
        tags = entry['tags']
        tag_list = [tag_1, tag_2]
        tag_list.extend(tags)

        # check if it already exists and get the tags

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
            errors += 1
            print(f'\nprocess_indicator failed with error:\n{e}')
            logfile = logfile + '\nupdate_indicator failed: ' + \
            str(entry) + str(e)

    logstring = f'\n\nFinished job for {infile}: {str(x)}' \
        f' indicators added, {str(y)} updated and {errors} errors.'
    print(highlight(logstring, 'yellow'))
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
        print(highlight( \
            f'\n{len(indicator_list)} Indicators imported from file', 'yellow'))
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
                tags = [x.lower() for x in input_list[2:]]
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
        f.write('\nEnd of log file: ' + filename + '\n\n')
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
    for infile in args:
        logfile = 'Log File\n'
        data_list = get_indicators(infile)
        process_indicator(data_list, infile)
        write_logfile(infile)
        #print(logfile)


if __name__ == "__main__":
    main()
