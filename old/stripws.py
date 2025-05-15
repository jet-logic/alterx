def stripWS(cur, ps = None):
	ps = ((1 == cur.nodeType) and (cur.getAttribute('xml:space') == 'preserve')) or ps;
	e = cur.firstChild;
	while e:
		(n, t, e) = (e, e.nodeType, e.nextSibling);
		if 1 == t:
			stripWS(n, ps);
		elif (t == n.TEXT_NODE) and not ps:
			t = n.data.strip();
			if len(t) > 0:
				n.data = t;
			else:
				cur.removeChild(n);
	return cur;

params = {};

def on_xml_start(ctx):
	print('on_xml_start: ' + repr(params.get('html')));

def on_xml_args(ctx, opt):
	print('on_xml_args: ' + repr(params.get('html')));
	if opt.is_bool('html'):
		params['html'] = opt.bool;

def on_xml_end(ctx):
	print('on_xml_end ' + repr(params.get('html')));

def on_xml_doc(doc, ctx):
	#~ print('on_xml_doc ' + ctx.filePath);
	stripWS(doc);
	return True;

