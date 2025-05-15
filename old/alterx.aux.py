##inconce <say2.py>
##inconce <say1.py>
##inconce <iteropt.py>
##inconce <dosGlob2RE.py>
##inconce <Counter.py>
##include <domTighten.py>
##inconce <domWriteXML.py>

def getDecl(f):
	decl = {};
	def onDecl(version, encoding, standalone):
		decl['version'] = version;
		decl['encoding'] = encoding;
		decl['standalone'] = standalone;
	from xml.parsers.expat import ParserCreate;
	p = ParserCreate()
	p.XmlDeclHandler = onDecl;
	if hasattr(f, 'read'):
		p.ParseFile(f);
	else:
		f = open(f, 'rb');
		try:
			p.ParseFile(f);
		finally:
			f.close();
	return decl;

class Sink:
	def __init__(self, out, enc):
		self.out = out;
		self.enc = enc;
	def write(self, x):
		self.out.write(x.encode(self.enc, 'xmlcharrefreplace'));
	def close(self,):
		pass

class SinkRaw:
	def __init__(self, out, enc):
		self.out = out;
		self.enc = enc;
	def write(self, x):
		self.out.write(x);
	def close(self,):
		pass

class HashSink(object):
	__slots__ = ('h',)
	def __init__(self, h = None):
		if not h:
			from hashlib import md5;
			h = md5();
		self.h = h;
	def write(self, x):
		self.h.update(x);

import re
re_sw = re.compile("\s+")
def stripWS(cur, ps = None):
	ps = ((1 == cur.nodeType) and (cur.getAttribute('xml:space') == 'preserve')) or ps
	e = cur.firstChild
	while e:
		(n, t, e) = (e, e.nodeType, e.nextSibling)
		if 1 == t:
			stripWS(n, ps)
		elif (t == n.TEXT_NODE) and not ps:
			t = n.data.strip()
			if len(t) > 0:
				n.data = re_sw.sub(' ', t)
			else:
				cur.removeChild(n)
	return cur

def hashXMLNode(node):
	from hashlib import md5;
	class hashSink:
		def __init__(self, h):
			self.h = h;
		def write(self, x):
			self.h.update(x.encode('UTF-8'));
	h = md5();
	s = hashSink(h);
	node.writexml(s);
	return h.hexdigest();

def domLoadDoc(file, opt):
	from xml.dom.minidom import parse
	doc = parse(file)
	if opt.modeHTML:
		(opt.stripWS or opt.savePretty) and domTighten(doc)
	else:
		opt.stripWS and stripWS(doc)
	return doc

def domWriteDoc(doc, out, enc, ctx):
	w = ctx.domWriter
	w.encoding = enc
	w.writexml(out, doc)

from os import listdir;
from os.path import join;
import logging;
def listdr(f0):
	try:
		return listdir(f0.path);
	except:
		logging.exception("Failed to list %r", f0.path);
	return ();

class fsinfo:
	def __init__(self, p):
		self.path= p;
	def __getattr__(self, name):
		if name == 'stat':
			from os import stat;
			self.__dict__[name] = stat(self.path);
		elif name in ('parent', 'name'):
			from os.path import split;
			(self.__dict__['parent'], self.__dict__['name']) = split(self.path);
		elif 'isdir' == name:
			from stat import S_ISDIR;
			self.__dict__[name] = bool(S_ISDIR(self.stat.st_mode));
		elif hasattr(self.stat, name):
			self.__dict__[name] = getattr(self.stat, name);
		return self.__dict__[name];

def walk_dir_pre(f0):
	d2 = f0.depth + 1;
	for name in listdr(f0):
		f1 = f0.__class__(join(f0.path, name));
		f1.depth = d2;
		f1.rel = join(f0.rel, name);
		f1.walk = None;
		yield f1;
		if f1.walk:
			for x in walk_dir_pre(f1):
				yield x;

def loadModule(ctx, value):
	from imp import find_module, load_module;
	from os.path import splitext, basename, isfile, dirname;
	(mo, parent, title) = (None, dirname(value), basename(value));
	if isfile(value):
		(title, _) = splitext(title);
	if parent:
		mo = find_module(title, [parent])
	else:
		mo = find_module(title)
	if mo:
		mo = load_module(title, *mo);
	return mo;
