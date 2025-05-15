
NS_RDF = 'http://www.w3.org/1999/02/22-rdf-syntax-ns#';

def on_desc(cur, ctx):
	about = cur.getAttributeNS(NS_RDF, 'about');
	e = cur.firstChild;
	while e:
		(n, t, e) = (e, e.nodeType, e.nextSibling);
		if 1 == t:
			print (about, n.namespaceURI, n.localName, n.firstChild and n.firstChild.data );

def on_xml_doc(doc, ctx):
	cur = doc.documentElement;
	e = cur.firstChild;
	while e:
		(n, t, e) = (e, e.nodeType, e.nextSibling);
		if 1 == t and n.namespaceURI == NS_RDF and n.localName == 'Description':
			on_desc(n, ctx);
				
