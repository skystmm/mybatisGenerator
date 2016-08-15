#!/usr/bin/env python
# -*- coding: utf-8 -*-
# author      Administrator
# created on  2016/08/12

import xlrd
import os

typeMap = {
            'bigint': 'Long',
            'int': 'Integer',
            'double': 'Double',
            'varchar': 'String',
            'varchar2': 'String',
            'date': 'Date',
            'float': 'Float',
            'tinyint': 'Integer',
           }

table_map = {}
table_index = ['t', 'biz', 'admin', ]


def read_info(path, files):
    if isinstance(files, list):
        for f in list:
            read_info(path, files)
    if isinstance(files, str):
        file = os.path.join(path, files)
        with xlrd.open_workbook(file) as xls:
            sheets = xls.sheets()
            for sheet in sheets:
                name = sheet.name
                rows = sheet.nrows
                if rows == 0:
                    continue
                li = []
                for x in xrange(1, rows):
                    column = sheet.cell(x, 0).value
                    c_type = sheet.cell(x, 1).value
                    desc = sheet.cell(x, 2).value
                    li.append([column.encode('utf-8'), c_type.encode('utf-8'), desc.encode('utf-8')])
                table_map[name] = li
        return table_map


def underline_to_camel(name):
    camel_format = ''
    if isinstance(name, basestring):
        if isinstance(name, unicode):
            name = name.encode('utf-8')
        for s in name.split('_'):
            camel_format += s.capitalize()
        camel_format = camel_format[0].lower() + camel_format[1:]
    return camel_format


def get_bean_name(name):
    bean_name = ''
    if isinstance(name, basestring):
        if isinstance(name, unicode):
            name = name.encode('utf-8')
        for s in name.split("_"):
            if s == 't' or s == 'biz':
                continue
            bean_name += s.capitalize()
    return bean_name
