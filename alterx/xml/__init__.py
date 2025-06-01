from argparse import ArgumentParser
from typing import Sequence
from ..app import App
from ..main import flag
from ..utils import HashSink

# strip_cdata - replace CDATA sections by normal text content (on by default)
# resolve_entities - replace entities by their text value (on by default)
# compact - use compact storage for short text content (on by default)


class AlterXMLET(App):
    tag = "XML"
    etree: object
    default_glob_includes = (r"*.xml", r"*.svg", r"*.xsd")
    xml_declaration: bool = flag("xml-declaration", "Add xml declaration", default=None)

    def _get_etree(self):
        import xml.etree.ElementTree as etree

        return etree

    # def parse_arguments(self, argp: ArgumentParser, args: Sequence[str] | None) -> None:
    #     return super().parse_arguments(argp, args)

    def parse_source(self, src: object):
        etree = self.etree
        kwargs = {}
        parser = etree.XMLParser(**kwargs)
        # etree: XMLParser(*, target=None, encoding=None)
        return etree.parse(src, parser)

    def hash_of(self, doc):
        h = HashSink()
        doc.write(h)
        return h.digest.hexdigest()

    def dump(self, doc: object, out: object, encoding: str):
        kwargs = {"method": "xml"}
        if self.xml_declaration is True:
            kwargs["xml_declaration"] = True
        # kwargs["xml_declaration"] = None
        # kwargs["default_namespace"] = None
        # kwargs["short_empty_elements"] = True
        doc.write(out, **kwargs)
        # etree: write(file, encoding='us-ascii', xml_declaration=None, default_namespace=None, method='xml', *, short_empty_elements=True)


class AlterXML(AlterXMLET):
    save_pretty: bool = flag("pretty", "Save pretty formated", default=None)
    ns_clean: bool = flag(
        "ns-clean", "Try to clean up redundant namespace declarations", default=False
    )
    recover: bool = flag(
        "recover", "Try hard to parse through broken XML", default=False
    )
    strip_ws: bool = flag(
        "strip-ws", "Discard blank text nodes between tags", default=False
    )
    strip_comments: bool = flag("strip-comments", "Discard comments", default=False)
    strip_pis: bool = flag("strip-pi", "Discard processing instructions", default=False)

    # huge_tree - disable security restrictions and support very deep trees and very long text content (only affects libxml2 2.7+)

    def _get_etree(self):
        from lxml import etree

        return etree

    def parse_source(self, src: object):
        etree = self.etree
        kwargs = {}
        kwargs["remove_blank_text"] = self.strip_ws
        kwargs["remove_comments"] = self.strip_comments
        kwargs["remove_pis"] = self.strip_pis
        # kwargs["strip_cdata"] = self.strip_cdata
        # lxml: XMLParser(self, encoding=None, attribute_defaults=False, dtd_validation=False, load_dtd=False, no_network=True, ns_clean=False, recover=False, schema: XMLSchema=None, huge_tree=False, remove_blank_text=False, resolve_entities=True, remove_comments=False, remove_pis=False, strip_cdata=True, collect_ids=True, target=None, compact=True)
        parser = etree.XMLParser(**kwargs)
        return etree.parse(src, parser)

    def dump(self, doc: object, out: object, encoding: str):
        kwargs = {"method": "xml"}
        kwargs["pretty_print"] = self.save_pretty
        # _encoding = encoding or doc.docinfo.encoding

        if self.xml_declaration is True:
            _standalone = doc.docinfo.standalone
            _xml_version = doc.docinfo.xml_version
            _encoding = doc.docinfo.encoding or encoding
            if _encoding:
                kwargs["encoding"] = _encoding
            if _standalone:
                kwargs["standalone"] = _standalone
            if _xml_version:
                kwargs["xml_version"] = _xml_version
            kwargs["xml_declaration"] = True
        # if _standalone or _xml_version:
        #     if _standalone:
        #         kwargs["standalone"] = None
        #     # if _xml_version:
        #     #     kwargs["xml_version"] = None
        #     kwargs["xml_declaration"] = True
        # kwargs["xml_declaration"] = None
        # kwargs["default_namespace"] = None
        # kwargs["short_empty_elements"] = True
        # print([_standalone, _xml_version, _encoding])
        doc.write(out, **kwargs)
        # lxml: write(self, file, encoding=None, method="xml", pretty_print=False, xml_declaration=None, with_tail=True, standalone=None, doctype=None, compression=0, exclusive=False, inclusive_ns_prefixes=None, with_comments=True, strip_text=False)

    def encoding_of(self, doc: object, src: str) -> str:
        return doc.docinfo.encoding
