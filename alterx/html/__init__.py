from ..xml import AlterXML


class AlterHTML(AlterXML):
    tag = "HTML"
    default_re_includes = (r"(?s:[^/]+\.(html|htm))\Z",)

    def _get_etree(self):
        from lxml import etree

        return etree
