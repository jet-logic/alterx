import logging
from .utils import HashSink
from .app import App
from .main import flag


class AlterXMl(App):

    pretty: bool = flag("pretty", "Save pretty formated", default=None)
    is_lxml = False
    tag = "XML"

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

    def start(self):

        if not self.includes:
            from re import compile

            self.includes.append(compile(r"(?s:[^/]+\.(xml|svg|xsd))\Z"))
        # self.etree
        # print("vars", self.__dict__)

        super().start()

    def parse_file(self, src):
        etree = self.etree
        kwargs = {}
        # if self.is_lxml:
        #     kwargs["remove_blank_text"] = app.stripWS
        #     kwargs["remove_comments"] = app.stripComments
        #     kwargs["remove_pis"] = app.stripPIs
        #     kwargs["strip_cdata"] = app.stripCDatas
        parser = etree.XMLParser(**kwargs)
        return etree.parse(open(src, "rb"), parser)

    def hash_of(self, doc):
        h = HashSink()
        doc.write(h)
        return h.digest.hexdigest()

    def dump(self, doc: object, out: object, encoding: str):
        doc.write(
            out, xml_declaration=True, encoding=encoding, pretty_print=self.save_pretty
        )
        # encoding="us-ascii", xml_declaration=None, default_namespace=None, method="xml"

    def check_accept(self, x):
        return x.is_file() and super().check_accept(x)


(__name__ == "__main__") and AlterXMl().main()
