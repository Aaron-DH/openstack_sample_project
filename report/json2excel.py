# -*- coding:utf-8 -*-

import json
import xlwt
import xlrd
import urllib2


# Get Json string from http
def http_get(url):
    req = urllib2.Request(url)
    response = urllib2.urlopen(req)
    return response.read()


# Convert string to python format data
def processjson(inputJsonFile, url):
    jsonstr = http_get(url)
    jsonfile = json.loads(jsonstr)
    write2excel(jsonfile)


# As the value may be a list in a dict, generate the cell by iteration
def generate_cell(worksheet, row, column, List):
    tmp_column = column
    tmp_row = 0
    for index, element in enumerate(List):  # element is a dict
        label = 0     # mark if function go to the iteration
        column = tmp_column
        for k, v in element.items():
            print row, column
            worksheet.write(row, column, label=k)
            if not isinstance(v, list):
                worksheet.write(row+1, column, label=json.dumps(v))
            else:   # if value is a list, go to the iteration
                label = 1
                tmp_row, column = generate_cell(worksheet, row+1, column, v)
            column = column+1
        if label:
            row = tmp_row   # update the row when jump out from last iteration function
        else:
            row = row + 2
    return row, column - 1


def write2excel(List):
    workbook = xlwt.Workbook()
    worksheet = workbook.add_sheet('cpu_sheet')
    row = 0
    column = 0
    generate_cell(worksheet, row, column, List)
    workbook.save('cpu_meter.xls')

if __name__ == "__main__":
    FILE = 'JsonHbase.json'
    URL = 'http://103.227.81.159:18888/v1/samples?limit=10&meter=disk.allocation'
    processjson(FILE, URL)
