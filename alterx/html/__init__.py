from ..xml import AlterXML


class AlterHTML(AlterXML):
    tag = "HTML"
    default_glob_includes = (r"*.html", r"*.htm")

    def parse_file(self, src):
        etree = self.etree
        kwargs = {}
        kwargs["remove_blank_text"] = self.strip_ws
        kwargs["remove_comments"] = self.strip_comments
        kwargs["remove_pis"] = self.strip_pis
        # kwargs["strip_cdata"] = self.strip_cdata
        parser = etree.HTMLParser(**kwargs)
        with open(src, "rb") as h:
            return etree.parse(h, parser)

    def dump(self, doc: object, out: object, encoding: str):
        kwargs = {"method": "html"}
        kwargs["pretty_print"] = self.save_pretty
        doc.write(out, xml_declaration=True, encoding=encoding, **kwargs)
