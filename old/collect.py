props = {};
abouts = {'' : {}};

def type(cur, ctx, about):
	pass;

def col(cur, ctx, about):
	x = cur.getAttribute('property');
	if x:
		x = about.setdefault(x, {})
		x = x.setdefault(cur.localName, {});
		x['#'] = x.get('#', 0) + 1;
		x['?'] = 1;
	x = cur.getAttribute('typeof');
	if x:
		about = abouts.setdefault(x, {});
		about['_count'] = about.get('_count', 0) + 1;
		about.setdefault('_tag', set()).add(cur.localName);
	e = cur.firstChild;
	while e:
		(n, t, e) = (e, e.nodeType, e.nextSibling);
		if 1 == t:
			col(n, ctx, about);

def on_xml_doc(doc, ctx):
	col(doc.documentElement, ctx, abouts['']);

def on_xml_end(ctx):
	import pprint
	pp = pprint.PrettyPrinter()
	pp.pprint(abouts)

"""
alterx -p D:\local\wrx\python\alterx.py\collect.py -g *.html 
"""