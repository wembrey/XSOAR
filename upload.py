#!/usr/bin/env python

#import the modules we need
import requests
import json
import sys
import datetime
logfile = 'Log File\n'

#Import the conig file that has the connection details
import config

# Get Global variables from config file
tenant = config.tenant
apikey = config.apikey

#set the URL for the API
url = 'https://' + tenant + '.dev.demisto.live/indicator/create'

# get the name of the indicator file
infile = input('Enter the name of the indicator file in current directory: ')
if not bool(infile):
    print(f"\nYou didn't enter an input file name. Closing!")
    sys.exit()

# define a function to send the API call
def add_indicator(data_list):
    global logfile
    x = 0
    for entry in data_list:
        #build the payload string for the indicator in json
        indicator_type = entry['type']
        sourcebrands = ["local-database"]
        tag1 = 'unvalidated'
        tag2 = 'local-db'
        tag3 = entry['tag3']
        customfields = {"tags": [tag1, tag2, tag3]}
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

        response = requests.request("POST", url, headers=headers, data=payload)
        if response.ok == True:
            logfile+='\n' + value + ' - OK'
            x += 1
        else:
            logfile+='\n' + value + ' - Failed'
    print(f'Finished job: {x} indicators added.')

# define a function to get indicators and load to dictionary
def get_indicators():
    global logfile
    data_list = []
    # Check if zone conversion file was added and load it
    try:
        f = open(infile, 'r')
        indicators = f.read()
        indicator_list = indicators.split('\n')
        print(f'\nindicators imported from file: {infile}')
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

    for items in data_list:
        print(f'{items}')
    command = input(
        '\nIf these are wrong - press q to finish and start again or press [Enter] to continue: ')
    if str.lower(command) == 'q':
        sys.exit()
    return data_list


# define a function to write a log file
def write_logfile():
    global logfile
    filename = datetime.datetime.now().strftime("log_%d_%m_%Y_%H_%M.log")
    command = input('Write log file? (y/n)')
    if str.lower(command) != 'y':
        print(logfile)
        print('\nExiting now')
        sys.exit()
    try:
        print(f'Opening {filename}')
        f = open(filename, 'w')
        print(f'Writing data to file')
        f.write(logfile)
        print('Closing')
        f.close()
    except Exception as e:
        print(f'Operation failed with error:\n{e}')
        error_log = error_log + '\n' + str(e)
        print(logfile)
        print('\nExiting now')
        sys.exit()


def main():
    global logfile
    data_list = get_indicators()
    add_indicator(data_list)
    write_logfile()


if __name__ == "__main__":
    main()
