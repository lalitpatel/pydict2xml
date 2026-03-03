"""Convert a Python dictionary to XML using lxml."""

import datetime
import logging
from typing import Any

from lxml import etree

logger = logging.getLogger("dict2xml")


class Dict2XML:
    """
    Converts a Python dictionary to XML using the lxml.etree library.
    For more info see: http://lxml.de/tutorial.html
    """
    _xml = None

    def __init__(self, root_node_name, dictionary, force_cdata=False):
        """
        :param root_node_name: name of the root node
        :param dictionary: instance of a dict object that needs to be converted
        :param force_cdata: if true, all text nodes will be wrapped in <![CDATA[ ]]>
        """
        self._xml = etree.Element(root_node_name)
        self._convert(self._xml, dictionary, force_cdata=force_cdata)

    def to_xml_string(self, encoding='UTF-8', pretty_print=True, xml_declaration=True):
        """
        Convert the etree object to an XML byte string.

        :param encoding: encoding for the XML output. Default 'UTF-8'
        :param pretty_print: pretty print the XML with indentation. Default True
        :param xml_declaration: include the XML declaration tag. Default True
        :return: XML as bytes
        """
        return etree.tostring(self._xml, xml_declaration=xml_declaration, pretty_print=pretty_print,
                              encoding=encoding, method='xml')

    def get_etree_object(self):
        """Return the underlying lxml.etree.Element."""
        return self._xml

    def _convert(self, node, value, force_cdata=False):
        """
        Recursively traverse the dictionary to convert it to XML.

        :param node: the parent XML node
        :param value: value of the node
        :param force_cdata: if true, all text nodes will be wrapped in <![CDATA[ ]]>
        """
        logger.debug("Parent Tag {} {}".format(node.tag, self._to_string(node)))
        logger.debug("Value {}".format(value))
        if isinstance(value, dict):
            if '@attributes' in value:
                logger.debug("Found @attributes")
                attributes = value.pop('@attributes')
                for key in attributes.keys():
                    attributes[key] = self._serialize_value(attributes[key])
                node.attrib.update(attributes)
            if '@text' in value:
                logger.debug("Found @text")
                if force_cdata:
                    node.text = etree.CDATA(self._serialize_value(value.pop('@text')))
                else:
                    node.text = self._serialize_value(value.pop('@text'))
            if '@cdata' in value:
                logger.debug("Found @cdata")
                node.text = etree.CDATA(self._serialize_value(value.pop('@cdata')))
            for key, val in value.items():
                logger.debug('Creating sub node ' + key)
                sub_node = etree.SubElement(node, key)
                self._convert(sub_node, val, force_cdata)
        elif isinstance(value, list):
            # remove the placeholder node and recreate as sibling elements
            tag = node.tag
            parent = node.getparent()
            parent.remove(node)
            for val in value:
                sub_node = etree.SubElement(parent, tag)
                self._convert(sub_node, val, force_cdata)
        else:
            # text node
            if force_cdata:
                node.text = etree.CDATA(self._serialize_value(value))
            else:
                node.text = self._serialize_value(value)

    @staticmethod
    def _to_string(node):
        """
        Pretty print an XML node for debug logging.

        :param node: etree XML node to be printed
        :return: XML as bytes
        """
        return etree.tostring(node, xml_declaration=False, pretty_print=True, encoding='UTF-8', method='xml')

    @staticmethod
    def _serialize_value(value: Any):
        """
        Serialize a Python value for use in XML text or attributes.

        :param value: the value to serialize
        :return: string representation
        """
        if isinstance(value, bool):
            return 'true' if value else 'false'
        if isinstance(value, type(None)):
            return ''
        if isinstance(value, datetime.datetime):
            return value.isoformat()
        return str(value)
