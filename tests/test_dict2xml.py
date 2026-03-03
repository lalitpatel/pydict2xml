import copy
import datetime
from collections import OrderedDict

import pytest
from lxml import etree

from py_dict_xml import Dict2XML


def _xml_string(root_name, data, force_cdata=False):
    """Helper to get XML string without declaration."""
    return Dict2XML(root_name, data, force_cdata=force_cdata).to_xml_string(
        xml_declaration=False, pretty_print=False
    ).decode("UTF-8")


class TestEmptyDict:
    def test_empty_dict(self):
        result = _xml_string("books", {})
        assert result == "<books/>"


class TestTextValues:
    def test_direct_text(self):
        result = _xml_string("book", {"@text": 1984})
        assert result == "<book>1984</book>"

    def test_child_text(self):
        result = _xml_string("books", {"book": 1984})
        assert result == "<books><book>1984</book></books>"


class TestCdata:
    def test_cdata_key(self):
        result = _xml_string("title", {"@cdata": "Foundation"})
        assert "<![CDATA[Foundation]]>" in result

    def test_force_cdata(self):
        result = _xml_string("book", {"@text": "1984"}, force_cdata=True)
        assert "<![CDATA[1984]]>" in result


class TestAttributes:
    def test_attributes_only(self):
        data = {"@attributes": {"type": "fiction", "year": 2011, "bestsellers": True}}
        result = _xml_string("books", data)
        root = etree.fromstring(result.encode())
        assert root.attrib["type"] == "fiction"
        assert root.attrib["year"] == "2011"
        assert root.attrib["bestsellers"] == "true"

    def test_attributes_with_text(self):
        data = {"@attributes": {"type": "fiction"}, "@text": 1984}
        result = _xml_string("books", data)
        root = etree.fromstring(result.encode())
        assert root.attrib["type"] == "fiction"
        assert root.text == "1984"

    def test_attributes_with_child(self):
        data = {"@attributes": {"type": "fiction"}, "book": 1984}
        result = _xml_string("books", data)
        root = etree.fromstring(result.encode())
        assert root.attrib["type"] == "fiction"
        assert root.find("book").text == "1984"


class TestChildren:
    def test_nested_children(self):
        data = {"@attributes": {"type": "fiction"}, "book": 1984}
        result = _xml_string("books", data)
        root = etree.fromstring(result.encode())
        assert root.find("book").text == "1984"

    def test_list_children(self):
        data = {
            "@attributes": {"type": "fiction"},
            "book": ["1984", "Foundation", "Stranger in a Strange Land"],
        }
        result = _xml_string("books", data)
        root = etree.fromstring(result.encode())
        books = root.findall("book")
        assert len(books) == 3
        assert books[0].text == "1984"
        assert books[1].text == "Foundation"
        assert books[2].text == "Stranger in a Strange Land"


class TestSerialization:
    def test_bool_true(self):
        data = {"@attributes": {"available": True}}
        result = _xml_string("book", data)
        root = etree.fromstring(result.encode())
        assert root.attrib["available"] == "true"

    def test_bool_false(self):
        data = {"@attributes": {"available": False}}
        result = _xml_string("book", data)
        root = etree.fromstring(result.encode())
        assert root.attrib["available"] == "false"

    def test_none_value(self):
        data = {"@attributes": {"available": None}}
        result = _xml_string("book", data)
        root = etree.fromstring(result.encode())
        assert root.attrib["available"] == ""

    def test_datetime(self):
        dt = datetime.datetime(2023, 6, 15, 12, 30, 0)
        data = {"@text": dt}
        result = _xml_string("timestamp", data)
        assert "2023-06-15T12:30:00" in result


class TestComplexExample:
    def test_ordered_dict_books(self):
        data = OrderedDict(
            {
                "@attributes": {"type": "fiction"},
                "book": [
                    {
                        "@attributes": {
                            "author": "George Orwell",
                            "available": None,
                        },
                        "title": "1984",
                        "isbn": 973523442132,
                    },
                    {
                        "@attributes": {
                            "author": "Isaac Asimov",
                            "available": False,
                        },
                        "title": {"@cdata": "Foundation"},
                        "price": "$15.61",
                        "isbn": 57352342132,
                    },
                    {
                        "@attributes": {
                            "author": "Robert A Heinlein",
                            "available": True,
                        },
                        "title": {"@cdata": "Stranger in a Strange Land"},
                        "price": {
                            "@attributes": {"discount": "10%"},
                            "@text": "$18.00",
                        },
                        "isbn": 341232132,
                    },
                ],
            }
        )
        result = _xml_string("books", data)
        root = etree.fromstring(result.encode())
        assert root.attrib["type"] == "fiction"
        books = root.findall("book")
        assert len(books) == 3
        assert books[0].attrib["author"] == "George Orwell"
        assert books[0].attrib["available"] == ""
        assert books[1].attrib["available"] == "false"
        assert books[2].attrib["available"] == "true"
        assert books[2].find("price").attrib["discount"] == "10%"
        assert books[2].find("price").text == "$18.00"


class TestEtreeObject:
    def test_get_etree_object(self):
        d = Dict2XML("root", {"child": "value"})
        obj = d.get_etree_object()
        assert isinstance(obj, etree._Element)
        assert obj.tag == "root"


class TestXmlDeclaration:
    def test_with_declaration(self):
        result = Dict2XML("root", {}).to_xml_string(xml_declaration=True).decode("UTF-8")
        assert result.startswith("<?xml")

    def test_without_declaration(self):
        result = Dict2XML("root", {}).to_xml_string(xml_declaration=False).decode("UTF-8")
        assert not result.startswith("<?xml")


class TestInputNotMutated:
    def test_dict_not_mutated(self):
        data = {
            "@attributes": {"type": "fiction"},
            "@text": "hello",
            "child": "value",
        }
        original = copy.deepcopy(data)
        _xml_string("root", data)
        assert data == original

    def test_nested_dict_not_mutated(self):
        data = {
            "book": {
                "@attributes": {"author": "Orwell"},
                "@cdata": "1984",
            }
        }
        original = copy.deepcopy(data)
        _xml_string("books", data)
        assert data == original

    def test_list_children_not_mutated(self):
        data = {
            "@attributes": {"type": "fiction"},
            "book": [
                {"@attributes": {"id": "1"}, "title": "1984"},
                {"@attributes": {"id": "2"}, "title": "Foundation"},
            ],
        }
        original = copy.deepcopy(data)
        _xml_string("books", data)
        assert data == original

    def test_can_convert_same_dict_twice(self):
        data = {
            "@attributes": {"type": "fiction"},
            "book": "1984",
        }
        result1 = _xml_string("books", data)
        result2 = _xml_string("books", data)
        assert result1 == result2


class TestInputValidation:
    def test_non_dict_raises_type_error(self):
        with pytest.raises(TypeError, match="dictionary must be a dict"):
            Dict2XML("root", "not a dict")

    def test_none_raises_type_error(self):
        with pytest.raises(TypeError, match="dictionary must be a dict"):
            Dict2XML("root", None)

    def test_list_raises_type_error(self):
        with pytest.raises(TypeError, match="dictionary must be a dict"):
            Dict2XML("root", [1, 2, 3])


class TestEdgeCases:
    def test_special_xml_characters_in_text(self):
        data = {"@text": '<script>alert("xss")</script>'}
        result = _xml_string("node", data)
        root = etree.fromstring(result.encode())
        assert root.text == '<script>alert("xss")</script>'
        assert "<script>" not in result  # should be escaped

    def test_ampersand_in_text(self):
        data = {"@text": "Tom & Jerry"}
        result = _xml_string("title", data)
        root = etree.fromstring(result.encode())
        assert root.text == "Tom & Jerry"

    def test_unicode_values(self):
        data = {"@text": "日本語テスト"}
        result = _xml_string("node", data)
        root = etree.fromstring(result.encode())
        assert root.text == "日本語テスト"

    def test_deeply_nested_dict(self):
        data = {"a": {"b": {"c": {"d": "deep"}}}}
        result = _xml_string("root", data)
        root = etree.fromstring(result.encode())
        assert root.find(".//d").text == "deep"

    def test_empty_string_text(self):
        data = {"@text": ""}
        result = _xml_string("node", data)
        # lxml distinguishes between no text (self-closing) and empty text
        assert result == "<node></node>"

    def test_integer_value(self):
        data = {"@text": 42}
        result = _xml_string("node", data)
        assert result == "<node>42</node>"

    def test_float_value(self):
        data = {"@text": 3.14}
        result = _xml_string("node", data)
        assert result == "<node>3.14</node>"

    def test_empty_list(self):
        data = {"book": []}
        result = _xml_string("books", data)
        # empty list produces no child elements
        root = etree.fromstring(result.encode())
        assert root.findall("book") == []

    def test_single_item_list(self):
        data = {"book": ["1984"]}
        result = _xml_string("books", data)
        root = etree.fromstring(result.encode())
        books = root.findall("book")
        assert len(books) == 1
        assert books[0].text == "1984"

    def test_cdata_overwrites_text(self):
        # when both @text and @cdata are present, @cdata wins (processed second)
        data = {"@text": "plain", "@cdata": "wrapped"}
        result = _xml_string("node", data)
        assert "<![CDATA[wrapped]]>" in result
        assert "plain" not in result


class TestForceCdata:
    def test_force_cdata_on_child_text(self):
        data = {"book": "1984"}
        result = _xml_string("books", data, force_cdata=True)
        assert "<![CDATA[1984]]>" in result

    def test_force_cdata_on_list_children(self):
        data = {"book": ["1984", "Foundation"]}
        result = _xml_string("books", data, force_cdata=True)
        assert result.count("<![CDATA[") == 2

    def test_force_cdata_with_cdata_key(self):
        # @cdata key + force_cdata should both produce CDATA
        data = {"title": {"@cdata": "Foundation"}}
        result = _xml_string("book", data, force_cdata=True)
        assert "<![CDATA[Foundation]]>" in result


class TestPrettyPrint:
    def test_pretty_print_true(self):
        data = {"book": "1984"}
        result = Dict2XML("books", data).to_xml_string(
            xml_declaration=False, pretty_print=True
        ).decode("UTF-8")
        assert "\n" in result
        assert "  <book>" in result

    def test_pretty_print_false(self):
        data = {"book": "1984"}
        result = Dict2XML("books", data).to_xml_string(
            xml_declaration=False, pretty_print=False
        ).decode("UTF-8")
        assert "\n" not in result
