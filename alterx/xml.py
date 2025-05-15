import logging
from .utils import HashSink
from .app import App
from .main import flag


class AlterXMl(App):

    save_pretty: bool = flag("pretty", "Save pretty formated", default=None)
    use_lxml: bool = flag("lxml", "Use lxml", default=None)
    tag = "XML"

    def _get_etree(self):
        if self.use_lxml is True:
            from lxml import etree

            return etree
        elif self.use_lxml is False:
            import xml.etree.ElementTree as etree

            return etree
        try:
            from lxml import etree

            self.use_lxml = True

            return etree
        except ImportError:
            try:  # Normal ElementTree install
                import xml.etree.ElementTree as etree

                self.use_lxml = False
                return etree
            except ImportError:
                logging.exception("Failed to import ElementTree from any known place")

    def ready(self) -> None:

        return super().ready()

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

    def dump(self, doc: object, out: object, encoding: str):
        kwargs = {}
        if self.use_lxml:
            kwargs["pretty_print"] = self.save_pretty

        doc.write(out, xml_declaration=True, encoding=encoding, **kwargs)
        # encoding="us-ascii", xml_declaration=None, default_namespace=None, method="xml"

    def check_accept(self, x):
        return x.is_file() and super().check_accept(x)


(__name__ == "__main__") and AlterXMl().main()
