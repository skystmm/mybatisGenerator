#!/usr/bin/env python
# -*- coding: utf-8 -*-
# author      Administrator
# created on  2016/08/12
import common
import xml.dom.minidom as dom


class CreateMapper(object):
    bean = 'private %s %s;\r\n'
    clazz = 'public class %s {\r\n'
    output_path = './%s/%s.%s'

    drop_sql = 'DROP TABLE IF EXISTS `%s`;\r\n'
    table_sql = 'CREATE TABLE `%s` (\r\n'
    column_sql = '`%s`  %s ,\r\n'
    primary = 'PRIMARY KEY (`%s`)\r\n'

    def __init__(self, path, files):
        self.path = path
        self.files = files
        self.table_map = common.read_info(self.path, self.files)

    def create_bean(self):
        for x in self.table_map.keys():
            li = self.table_map[x]
            class_name = common.get_bean_name(x)
            properties = []
            properties.append(self.clazz % class_name)
            for c in li:
                column = c[0]
                type_name = c[1]
                properties.append(
                    self.bean % (common.typeMap.get(type_name.split('(')[0]), common.underline_to_camel(column)))
            properties.append('}')
            self.wirte_to_file('bean', class_name, 'java', properties)

    def create_sql(self):
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
        if type == 'sql':
            mode = 'a'
        else:
            mode = 'w'
        with open(self.output_path % (type, name, tail), mode) as f:
            for p in content:
                f.write(p)

    def create_mapper(self):
        for table_name in self.table_map.keys():
            li = self.table_map[table_name]
            properties = []
            class_name = common.get_bean_name(table_name)
            mapper = '%s%s' % (class_name, 'Mapper')
            self.generate_xml(table_name, class_name, mapper, li)

    def generate_xml(self, table_name, class_name, mapper, content):
        base_select = "\r\nselect * from %s where 1=1\r\n" % table_name
        impl = dom.getDOMImplementation()
        type = dom.DocumentType('mapper')
        type.publicId = "-//mybatis.org//DTD Mapper 3.0//EN"
        type.systemId = "http://mybatis.org/dtd/mybatis-3-mapper.dtd"

        xml = impl.createDocument(None, 'mapper', type)
        root = xml.documentElement
        root.setAttribute("namespace", mapper)  # 增加属性
        resultMap = xml.createElement('resultMap')
        resultMap.setAttribute('id', 'BaseResultMap')
        resultMap.setAttribute('type', class_name)
        root.appendChild(resultMap)

        sid_tag = xml.createElement('select')
        sid_tag.setAttribute("id", "selectById")
        sid_tag.setAttribute("resultMap", 'BaseResultMap')
        select_date = xml.createTextNode(
            "%s and %s = #{%s}" % (base_select, content[0][0], common.underline_to_camel(content[0][0])))
        sid_tag.appendChild(select_date)
        root.appendChild(sid_tag)

        select_tag = xml.createElement('select')
        select_tag.setAttribute("id", "selectBy")
        select_tag.setAttribute("resultMap", 'BaseResultMap')
        select_tag.appendChild(xml.createTextNode(base_select))
        root.appendChild(select_tag)

        insert_tag = xml.createElement('insert')
        insert_tag.setAttribute("id", "insert")
        insert_tag.setAttribute("paramterType", class_name)
        insert_tag.appendChild(xml.createTextNode("insert into %s "))
        trim1_tag = xml.createElement("trim")

        # prefix="(" suffix=")" suffixOverrides=","
        trim1_tag.setAttribute("prefix", "(")
        trim1_tag.setAttribute("suffix", ")")
        trim1_tag.setAttribute("suffixOverrides", ",")

        trim2_tag = xml.createElement("trim")
        trim2_tag.setAttribute("prefix", "values (")
        trim2_tag.setAttribute("suffix", ")")
        trim2_tag.setAttribute("suffixOverrides", ",")

        insert_tag.appendChild(trim1_tag)
        insert_tag.appendChild(trim2_tag)

        root.appendChild(insert_tag)

        update_tag = xml.createElement('update')
        update_tag.setAttribute("id", 'update')
        update_tag.setAttribute("paramterType", class_name)
        update_tag.appendChild(xml.createTextNode("update %s " % table_name))

        set_tag = xml.createElement("set")
        update_tag.appendChild(set_tag)
        root.appendChild(update_tag)

        delete_tag = xml.createElement("delete")
        delete_tag.appendChild(xml.createTextNode(
            "delete from %s where %s = #{%s}" % (table_name, content[0][0], common.underline_to_camel(content[0][0]))))
        root.appendChild(delete_tag)

        for x in content:
            tag = None
            if_tag = xml.createElement('if')
            key_tag = xml.createElement('if')
            value_tag = xml.createElement('if')
            up_tag = xml.createElement('if')
            if x[0] == 'id':
                tag = xml.createElement('id')
            else:
                tag = xml.createElement('column')

            tag.setAttribute("column", x[0])
            tag.setAttribute("property", common.underline_to_camel(x[0]))
            resultMap.appendChild(tag)

            if_tag.setAttribute("test", "%s != null" % common.underline_to_camel(x[0]))
            if_tag.appendChild(xml.createTextNode(" and %s = #{%s}" % (x[0], common.underline_to_camel(x[0]))))
            select_tag.appendChild(if_tag)

            value_tag.setAttribute("test", "%s != null" % common.underline_to_camel(x[0]))
            value_tag.appendChild(xml.createTextNode('#{%s},' % common.underline_to_camel(x[0])))
            trim2_tag.appendChild(value_tag)

            key_tag.setAttribute("test", "%s != null" % common.underline_to_camel(x[0]))
            key_tag.appendChild(xml.createTextNode(x[0] + ','))
            trim1_tag.appendChild(key_tag)

            up_tag.setAttribute("test", "%s != null" % common.underline_to_camel(x[0]))
            up_tag.appendChild(xml.createTextNode("%s = #{%s}," % (x[0], common.underline_to_camel(x[0]))))
            set_tag.appendChild(up_tag)
        update_tag.appendChild(
            xml.createTextNode("where %s = #{%s} " % (content[0][0], common.underline_to_camel(content[0][0]))))
        with open(self.output_path % ('xml', mapper, 'xml'), 'w')as f:
            xml.writexml(f, addindent='  ', newl='\n')


if __name__ == '__main__':
    cm = CreateMapper('./', 'yht.xls')
    cm.create_bean()
    cm.create_sql()
    cm.create_mapper()
