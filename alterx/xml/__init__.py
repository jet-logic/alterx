import logging
from ..app import App
from ..main import flag

# ns_clean - try to clean up redundant namespace declarations
# recover - try hard to parse through broken XML
# remove_blank_text - discard blank text nodes between tags, also known as ignorable whitespace. This is best used together with a DTD or schema (which tells data and noise apart), otherwise a heuristic will be applied.
# remove_comments - discard comments
# remove_pis - discard processing instructions
# strip_cdata - replace CDATA sections by normal text content (on by default)
# resolve_entities - replace entities by their text value (on by default)
# huge_tree - disable security restrictions and support very deep trees and very long text content (only affects libxml2 2.7+)
# compact - use compact storage for short text content (on by default)


class AlterXMLET(App):
    tag = "XML"
    etree: object
    default_re_includes = (r"(?s:[^/]+\.(xml|svg|xsd))\Z",)

    def _get_etree(self):
        import xml.etree.ElementTree as etree

        return etree

    def parse_file(self, src):
        etree = self.etree
        kwargs = {}
        parser = etree.XMLParser(**kwargs)
        return etree.parse(open(src, "rb"), parser)

    def dump(self, doc: object, out: object, encoding: str):
        kwargs = {}

        doc.write(out, xml_declaration=True, encoding=encoding, **kwargs)


class AlterXML(AlterXMLET):

    save_pretty: bool = flag("pretty", "Save pretty formated", default=None)
    # use_lxml: bool = flag("lxml", "Use lxml", default=None)

    def _get_etree(self):

        from lxml import etree

        return etree

    def parse_file(self, src):
        etree = self.etree
        kwargs = {}
        # if self.is_lxml:
        #     kwargs["remove_blank_text"] = app.stripWS
        #     kwargs["remove_comments"] = app.stripComments
        #     kwargs["remove_pis"] = app.stripPIs
        #     kwargs["strip_cdata"] = app.stripCDatas
        # lxml: XMLParser(self, encoding=None, attribute_defaults=False, dtd_validation=False, load_dtd=False, no_network=True, ns_clean=False, recover=False, schema: XMLSchema=None, huge_tree=False, remove_blank_text=False, resolve_entities=True, remove_comments=False, remove_pis=False, strip_cdata=True, collect_ids=True, target=None, compact=True)
        # etree: XMLParser(*, target=None, encoding=None)
        parser = etree.XMLParser(**kwargs)
        return etree.parse(open(src, "rb"), parser)

    def dump(self, doc: object, out: object, encoding: str):
        kwargs = {}
        kwargs["pretty_print"] = self.save_pretty

        doc.write(out, xml_declaration=True, encoding=encoding, **kwargs)
        # etree: write(file, encoding='us-ascii', xml_declaration=None, default_namespace=None, method='xml', *, short_empty_elements=True)
        # lxml: write(self, file, encoding=None, method="xml", pretty_print=False, xml_declaration=None, with_tail=True, standalone=None, doctype=None, compression=0, exclusive=False, inclusive_ns_prefixes=None, with_comments=True, strip_text=False)
