lm={
'xmp':['href',],
'embed':['pluginspage','src',],
'tr':['background',],
'object':['classid','codebase','data','archive','usemap',],
'input':['src','usemap',],
'a':['href',],
'area':['href',],
'table':['background',],
'form':['action',],
'img':['src','lowsrc','longdesc','usemap',],
'frame':['src','longdesc',],
'isindex':['action',],
'body':['background',],
'bgsound':['src',],
'th':['background',],
'link':['href',],
'base':['href',],
'script':['src','for',],
'head':['profile',],
'ilayer':['background',],
'del':['cite',],
'blockquote':['cite',],
'iframe':['src','longdesc',],
'ins':['cite',],
'layer':['background','src',],
'q':['cite',],
'td':['background',],
'applet':['archive','codebase','code',],
}

try:
	from urlparse import urlparse
except:
	from urllib.parse import urlparse

seen={}
opts={'root':False}
from sys import stdout,stderr
def on_xml_etree(doc, ctx):
	root = doc.getroot()
	for e in root.xpath(r"//*"):
		t = e.tag
		for v in lm.get(t, []):
			if opts.get('exres'):
				if v in ('href',):
					if t == 'link':
						rel = e.get("rel") or False
						if rel:
							rel = rel.strip().lower()
						if rel in ("alternate stylesheet", "stylesheet"):
							pass
						else:
							continue
					else:
						continue
				elif v in ('action',) and t == 'form':
					continue
			h = e.attrib.get(v)
			if not h:
				continue
			elif opts.get('root'):
				o = urlparse(h)
				s = o.scheme
				n = o.netloc
				if s:
					if opts.get('exres') and s == 'data':
						continue
					h = s + '://' + n
				elif n:
					h = n
			elif opts.get('exres'):
				o = urlparse(h)
				s = o.scheme
				if s and s == 'data':
					continue
			if h in seen:
				continue
			seen[h] = True
			try:
				x = opts.get('includes')
				if x:
					if 'abs' in x:
						o = urlparse(h)
						if not o.path.startswith("/"):
							continue
				if opts.get('extra'):
					stdout.write(t)
					stdout.write('\t')
					stdout.write(v)
					stdout.write('\t')
				stdout.write(h)
				stdout.write('\n')
			except:
				stderr.write("Failed %r\n" % h)

def on_xml_args(ctx, opt):
	if opt.is_bool('root'):
		opts['root'] = opt.bool
	elif opt.is_bool('external-resource', 'exres'):
		opts['exres'] = opt.bool
	elif opt.is_bool('extra'):
		opts['extra'] = opt.bool
	elif opt.is_string('include'):
		if 'includes' not in opts:
			opts['includes'] = set()
		opts['includes'].add(opt.string)

"""
alterx --html -p K:\wrx\python\alterx\links.py "K:\pub\007\Configure Android Studio _ Android Studio.html"
"""
