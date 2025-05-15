
from sys import stdout,stderr
def on_xml_etree(doc, ctx):
	for e in doc.getroot().xpath(r".//base"):
		e.tag = 'de' + e.tag
		stderr.write(e.get('href') + "\n")


