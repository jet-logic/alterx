
def on_xml_etree(doc, ctx):
	print("on_xml_etree")
	from lxml.html.clean import clean_html, Cleaner
	cleaner = Cleaner(scripts=True, embedded=True, meta=True, page_structure=True, links=True, style=True)
	cleaner.clean_html(doc)
