"""Convert XML to a Python dictionary using lxml."""

import logging
from collections import OrderedDict

from lxml import etree

logger = logging.getLogger("xml2dict")


class XML2Dict:
    """
    Converts XML to a Python dictionary using the lxml.etree library.
    For more info see: http://lxml.de/tutorial.html
    """
    _xml = None

    def __init__(self, xml, ns_clean=True):
        """
        :param xml: XML string or bytes to parse
        :param ns_clean: remove namespace prefixes. Default True
        """
        parser = etree.XMLParser(ns_clean=ns_clean, remove_blank_text=True)
        self._xml = etree.XML(xml, parser)

    def to_dict(self, ordered_dict=False):
        """
        Convert the parsed XML to a Python dictionary.

        :param ordered_dict: if True, return an OrderedDict instead of a dict
        :return: dict or OrderedDict representation of the XML
        """
        return self._convert(self._xml, ordered_dict)

    def get_etree_object(self):
        """Return the underlying lxml.etree.Element."""
        return self._xml

    def _convert(self, node, ordered_dict=False):
        """
        Recursively convert an XML node to a dictionary.

        :param node: the XML node to convert
        :param ordered_dict: if True, use OrderedDict
        :return: dict, OrderedDict, or string for text-only nodes
        """
        logger.debug("Parent Tag {} {}".format(node.tag, self._to_string(node)))
        xml_dict = OrderedDict() if ordered_dict else {}

        # add attributes and text nodes
        if len(node.attrib):
            xml_dict['@attributes'] = node.attrib
        if node.text:
            xml_dict['@text'] = node.text

        # add children if any
        if len(node):
            for child in node:
                if child.tag not in xml_dict:
                    # collect children into a list; single-element lists are flattened below
                    xml_dict[child.tag] = []
                xml_dict[child.tag].append(self._convert(child, ordered_dict))

            # flatten single-element lists
            for key, value in xml_dict.items():
                if type(value) == list and len(value) == 1:
                    xml_dict[key] = value[0]

        # flatten the dict if it just has the @text key
        if len(xml_dict) == 1 and '@text' in xml_dict:
            xml_dict = xml_dict['@text']

        return xml_dict

    @staticmethod
    def _to_string(node):
        """
        Pretty print an XML node for debug logging.

        :param node: etree XML node to be printed
        :return: XML as bytes
        """
        return etree.tostring(node, xml_declaration=False, pretty_print=True, encoding='UTF-8', method='xml')
