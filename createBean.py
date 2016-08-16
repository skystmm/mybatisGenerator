#!/usr/bin/env python
# -*- coding: utf-8 -*-
# author      skystmm
# created on  2016/08/12

import common
import xml.dom.minidom as dom


class CreateMapper(object):
    """
    from excel to create sql/java bean/mapper file.
    """
    bean = 'private %s %s;\r\n'
    clazz = 'public class %s {\r\n'
    output_path = './%s/%s.%s'

    drop_sql = 'DROP TABLE IF EXISTS `%s`;\r\n'
    table_sql = 'CREATE TABLE `%s` (\r\n'
    column_sql = '`%s`  %s ,\r\n'
    primary = 'PRIMARY KEY (`%s`)\r\n'

    def __init__(self, path, files, pack):
        self.path = path
        self.files = files
        self.table_map = common.read_info(self.path, self.files)
        self.package = pack

    def create_bean(self):
        """
        create java bean by sql info
        :return:
        """
        for x in self.table_map.keys():
            li = self.table_map[x]
            class_name = common.get_bean_name(x)
            properties = []
            if self.package is not None:
                properties.append("package %s;\r\n" % self.package)
            properties.append(self.clazz % class_name)
            for c in li:
                column = c[0]
                type_name = c[1]
                properties.append(
                    self.bean % (common.typeMap.get(type_name.split('(')[0]), common.underline_to_camel(column)))
            properties.append('}')
            self.wirte_to_file('bean', class_name, 'java', properties)

    def create_sql(self):
        """
        create sql file
        :return:
        """
        for table_name in self.table_map.keys():
            li = self.table_map[table_name]
            properties = []
            properties.append(self.drop_sql % table_name)
            properties.append(self.table_sql % table_name)
            for c in li:
                column = c[0]
                type_name = c[1]
                comment = c[2]
                if comment is not None and len(comment) > 0:
                    type_name = '%s COMMENT \'%s\'' % (type_name, comment)
                properties.append(self.column_sql % (column, type_name))
            properties.append(self.primary % li[0][0])
            properties.append(');\r\n')
            self.wirte_to_file('sql', 'tables', 'sql', properties)

    def wirte_to_file(self, type, name, tail, content):
        """
        write info into target file
        :param type:
        :param name:
        :param tail:
        :param content:
        :return:
        """
        if type == 'sql':
            mode = 'a'
        else:
            mode = 'w'
        with open(self.output_path % (type, name, tail), mode) as f:
            for p in content:
                f.write(p)

    def create_mapper(self):
        """
        create mybatis mapper.xml
        :return:
        """
        for table_name in self.table_map.keys():
            li = self.table_map[table_name]
            properties = []
            class_name = common.get_bean_name(table_name)
            mapper = '%s%s' % (class_name, 'Mapper')
            self.generate_xml(table_name, class_name, mapper, li)

    def generate_xml(self, table_name, class_name, mapper, content):
        """
        mybatis mapper.xml generate
        :param table_name:
        :param class_name:
        :param mapper:
        :param content:
        :return:
        """
        class_name = '%s.%s' % (self.package, class_name) if self.package is not None else class_name
        base_select = "\nselect * from %s where 1=1\n" % table_name
        impl = dom.getDOMImplementation()
        type = dom.DocumentType('mapper')
        type.publicId = "-//mybatis.org//DTD Mapper 3.0//EN"
        type.systemId = "http://mybatis.org/dtd/mybatis-3-mapper.dtd"

        self.xml = impl.createDocument(None, 'mapper', type)
        root = self.xml.documentElement
        root.setAttribute("namespace", mapper)  # 增加属性
        resultMap = self.tag_create('resultMap', root,
                                    attr={'id': 'BaseResultMap', 'type': class_name})

        self.tag_create('select', root, contents="%s and %s = #{%s}" % (
            base_select, content[0][0], common.underline_to_camel(content[0][0])),
                        attr={"id": "selectById", "resultMap": 'BaseResultMap'})

        select_tag = self.tag_create('select', root, contents=base_select,
                                     attr={"id": "selectBy", "resultMap": 'BaseResultMap'})

        insert_tag = self.tag_create('insert', root, contents="insert into %s " % table_name,
                                     attr={"id": "insert", "paramterType": class_name})

        trim1_tag = self.tag_create("trim", insert_tag, attr={"prefix": "(", "suffix": ")", "suffixOverrides": ","})

        trim2_tag = self.tag_create("trim", insert_tag,
                                    attr={"prefix": "values (", "suffix": ")", "suffixOverrides": ","})
        update_tag = self.tag_create('update', root, contents="update %s " % table_name,
                                     attr={'id': 'update', "paramterType": class_name})

        set_tag = self.tag_create('set', update_tag)

        self.tag_create('delete', root, contents="delete from %s where %s = #{%s}" % (
            table_name, content[0][0], common.underline_to_camel(content[0][0])),
                        attr={'id': 'delete', 'paramterType': class_name})

        for x in content:

            if x[0] == 'id':
                tag = self.xml.createElement('id')
            else:
                tag = self.xml.createElement('column')

            tag.setAttribute("column", x[0])
            tag.setAttribute("property", common.underline_to_camel(x[0]))
            resultMap.appendChild(tag)

            self.tag_create('if', select_tag, contents=" and %s = #{%s}" % (x[0], common.underline_to_camel(x[0])),
                            attr={"test": "%s != null" % common.underline_to_camel(x[0])})

            self.tag_create('if', trim2_tag, contents='#{%s},' % common.underline_to_camel(x[0]),
                            attr={"test": "%s != null" % common.underline_to_camel(x[0])})

            self.tag_create('if', trim1_tag, contents=x[0] + ',',
                            attr={"test": "%s != null" % common.underline_to_camel(x[0])})

            self.tag_create('if', set_tag, contents="%s = #{%s}," % (x[0], common.underline_to_camel(x[0])),
                            attr={"test": "%s != null" % common.underline_to_camel(x[0])})

        update_tag.appendChild(
            self.xml.createTextNode(
                "where %s = #{%s} " % (content[0][0], common.underline_to_camel(content[0][0]))))
        select_tag.appendChild(self.xml.createTextNode("order by %s desc" % content[0][0]))
        with open(self.output_path % ('xml', mapper, 'xml'), 'w')as f:
            self.xml.writexml(f, addindent='  ', newl='\n')

    def tag_create(self, tag_name, parent, contents=None, attr={}):
        """
        meethod fun : create xml tags
        :param tag_name:
        :param parent:
        :param contents:
        :param attr:
        :return:
        """
        tag = self.xml.createElement(tag_name)
        if isinstance(attr, dict) and len(attr) > 0:
            for key in attr.keys():
                tag.setAttribute(key, attr[key])
        if contents is not None and isinstance(contents, basestring):
            tag.appendChild(self.xml.createTextNode(contents))
        if isinstance(parent, dom.Document) or isinstance(parent, dom.Element):
            parent.appendChild(tag)
        elif isinstance(parent, basestring):
            parent = self.xml.getElementsByTagName(parent)
            if parent is not None:
                parent.appendChild(tag)
        return tag


if __name__ == '__main__':
    cm = CreateMapper('./', 'yht.xls', 'com.smht.yht.model')
    cm.create_bean()
    cm.create_sql()
    cm.create_mapper()
    # impl = dom.getDOMImplementation()
    # print type(impl)
    # xml = impl.createDocument(None, 'dads', None)
    # print isinstance(xml, dom.Document)
