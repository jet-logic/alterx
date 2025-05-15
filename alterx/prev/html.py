from .main import main
from .xml import XmlET


class HtmlET(XmlET):
    name_re = r"\.(html?)$"

    def parse_file(self, src, app):
        etree = self.etree
        kwargs = {}
        if self.is_lxml:
            kwargs["remove_blank_text"] = app.stripWS
            kwargs["remove_comments"] = app.stripComments
            kwargs["remove_pis"] = app.stripPIs
            kwargs["strip_cdata"] = app.stripCDatas
            from lxml import html

            with open(src, "rb") as si:
                return html.parse(si)
        else:
            kwargs["html"] = True
            with open(f, "rb") as h:
                return etree.parse(h, etree.XMLParser(**kwargs))

    def dump(self, O, out, encoding, app):
        kwargs = {}
        kwargs["method"] = "html"
        kwargs["xml_declaration"] = False
        kwargs["pretty_print"] = app.savePretty
        O.write(out, encoding=encoding, **kwargs)
        # write(file, encoding="us-ascii", xml_declaration=None, default_namespace=None, method="xml")

    def supply_argparse(self, parser):
        super().supply_argparse(parser)
        parser.description = "Alters HTML files"


__name__ == "__main__" and main(HtmlET())
