import logging
from . import HashSink, SinkRaw, Xml
from .main import main


class XmlET(Xml):
    id = "etree"

    # fn_call = ["on_etree", 'on_xml_etree']
    fn_call = "on_etree"
    fn_init = "on_etree_init"
    fn_start = "on_etree_start"
    fn_end = "on_etree_end"

    def _get_etree(self):
        try:
            from lxml import etree

            self.is_lxml = True

            return etree
        except ImportError:
            try:  # Normal ElementTree install
                import xml.etree.ElementTree as etree

                self.is_lxml = False
                return etree
            except ImportError:
                logging.exception("Failed to import ElementTree from any known place")

    def parse_file(self, src, app):
        etree = self.etree
        kwargs = {}
        if self.is_lxml:
            kwargs["remove_blank_text"] = app.stripWS
            kwargs["remove_comments"] = app.stripComments
            kwargs["remove_pis"] = app.stripPIs
            kwargs["strip_cdata"] = app.stripCDatas
        parser = etree.XMLParser(**kwargs)
        return etree.parse(open(src, "rb"), parser)

    def hash_of(self, O):
        h = HashSink()
        O.write(h)
        return h.h.hexdigest()

    def dump(self, O, out, encoding, app):
        O.write(
            out, xml_declaration=True, encoding=encoding, pretty_print=app.savePretty
        )
        # encoding="us-ascii", xml_declaration=None, default_namespace=None, method="xml"

    def sink_out(self, encoding):
        from sys import stdout

        return SinkRaw(stdout.buffer, encoding)

    def supply_argparse(self, parser):
        super().supply_argparse(parser)
        parser.add_argument(
            "--strip_ws", help="strip spaces", dest="stripWS", action="store_true"
        )
        parser.add_argument(
            "--strip_comment",
            help="strip comments",
            dest="stripComments",
            action="store_true",
        )
        parser.add_argument(
            "--strip_pi", help="strip pis", dest="stripPIs", action="store_true"
        )
        parser.add_argument(
            "--strip_cdata",
            help="strip cdatas",
            dest="stripCDatas",
            action="store_true",
        )

        # print(self.etree)
        parser.description = "Alters XML files"


__name__ == "__main__" and main(XmlET())
