#!/usr/bin/env python
NAME = "alterx.py";
VERSION = "1.1.2";
##inconce <alterx.aux.py>

def init_app(app):
	return
gCounterMap = {}
def getCounter(name):
	global gCounterMap
	if name not in gCounterMap:
		gCounterMap[name] = Counter()
	return gCounterMap[name]
TOT = getCounter('AlterX')

from os.path import abspath;
import logging
gUselxml = None
def onFile(f, ctx):
	ctx.filePath = f = abspath(f);
	TOT.Total += 1;
	# Load document
	try:
		ctx.domDoc = ctx.domParse(f);
	except:
		TOT.Error += 1;
		return logging.exception("Failed to load %r", f);
	else:
		logging.info("XML: %s %s", (ctx.domDoc and ("[#%d]" % TOT.Total) or "ERROR"), f);
		#~ say2("XML:", ctx.domDoc and ("[#%d]" % TOT.Total) or "ERROR", ctx.useEncoding or ctx.domEncoding(ctx.domDoc) or "ASCII", f);
	# Feed to plugins
	if ctx.checksModification:
		if ctx.modifyIf == 2:
			ctx.hashOfDOM = mHash = ctx.domHash(ctx.domDoc)
		else:
			mHash = None
			ctx.hashOfDOM = ctx.domHash(ctx.domDoc)
	else:
		mHash = (ctx.modifyIf == 2) and ctx.domHash(ctx.domDoc)
	mUrge = None;
	#TODO: optimize
	for _ in (_ for _ in (ctx.domCallStart, ctx.domCall, ctx.domCallEnd) if _):
		r = None
		for x in ctx.plugIns:
			r = getattr(x, _, None)
			#~ say1(x, _, r)
			if r and r(ctx.domDoc, ctx):
				mUrge = True; # call back says he modified it
	# Was modified?
	if mHash: # (ctx.modifyIf == 2) Modify if hash changed
		mSave = not (ctx.domHash(ctx.domDoc) == mHash);
	else:
		mSave = mUrge or (ctx.modifyIf > 2);
	if not mSave:
		return None;
	# Modified, Save it
	encoding = ctx.useEncoding or ctx.domEncoding(ctx.domDoc) or "ASCII";
	if (not ctx.dryRun):
		out = None
		if len(ctx.fileOut) < 1: # []
			out = ctx.domSinkFile(ctx.filePath, encoding)
		elif (len(ctx.fileOut) == 1) and (ctx.fileOut[0] == '-'): # ['-']
			out = ctx.domSinkOut(encoding)
		else: # ['file1', ...]
			out = ctx.domSinkFile(ctx.fileOut.pop(0), encoding)
		ctx.domWrite(ctx.domDoc, out, encoding, ctx)
		out = out.close();
		ctx.domDoc = None
	TOT.Altered += 1;
	logging.info("XML: Altered %s %r", (ctx.dryRun and '?' or '!'), encoding and ('[' + encoding + ']') or '');

class App(object):
	def __contains__(self, name):
		return (name in self.__dict__)
	def __setitem__(self, key, value):
		self.__dict__[key] = value
	def __getitem__(self, name):
		return getattr(self, name)

def main(app):
	app.stripWS = None
	app.stripPIs = None
	app.stripCDatas = None
	app.stripComments = None
	app.useLXML = None
	app.useEncoding = None
	app.useNL = ""
	app.useIndent = ""
	app.useTab = ""
	app.savePretty = None
	app.dryRun = None
	app.deBug = None
	app.modifyIf = 0
	app.fileOut = []
	app.fileInc = []
	app.plugIns = []
	app.nameRE = []
	app.modeHTML = None
	app.checksModification = None
	init_app(app)
	args = []
	mo = None
	### Logging
	from logging import basicConfig, INFO, DEBUG
	basicConfig(**{'level' : INFO, 'format' : '%(levelname)s: %(message)s'})
	opt = iteropt();
	while opt.next():
		if opt.is_plain():
			args.append(opt.plain)
	# Module:
		elif opt.is_string('plugin', 'p'):
			mo = None
			try:
				mo = loadModule(app, opt.string);
			finally:
				logging.info("XML: Module %r %r", mo and getattr(mo, '__name__', '') or '', opt.string);
			if mo:
				app.plugIns.append(mo);
				if app.useLXML is None and getattr(mo, 'on_xml_etree', None):
					app.useLXML = True
				if hasattr(mo, 'on_xml_init'): mo.on_xml_init(app)
				mo = getattr(mo, 'on_xml_args', None);
				# register_xml_class, register_xml_calback
		# If there is a module option callback, give him the first chance to pop the option.
		# If he pops an option, go to next. Notice that he can't use SHORT and PLAIN option
		elif mo and opt.is_long_form() and (mo(app, opt) or True) and (not opt.is_valid()):
			continue;
	# Misc:
		elif opt.is_bool('h', 'help'): # --help, --no-help, --help, -h
			pass
		elif opt.is_bool('dry-run', 'n'):
			app.dryRun = opt.bool;
		elif opt.is_bool('act'):
			if opt.bool:
				app.dryRun = False;
		elif opt.is_bool('debug'):
			app.deBug = opt.bool;
	# Pretty XML
		elif opt.is_bool('stripws'):
			app.stripWS = opt.bool;
		elif opt.is_bool('pretty'): # --pretty, --no-pretty, --nopretty
			app.useIndent = "";
			app.useTab = "\t";
			app.useNL = "\n";
			app.savePretty = True;
		elif opt.is_string('newl'):
			app.useNL = opt.string;
		elif opt.is_string('indent'):
			app.useIndent = opt.string;
		elif opt.is_string('add-indent'):
			app.useTab = opt.string;
	# Save
		elif opt.is_string('encoding'):
			app.useEncoding = opt.string;
		elif opt.is_string('o', 'out'):
			app.fileOut.append(opt.string);
		elif opt.is_string('i', 'include'): # -i FILE, --include FILE -iFILE
			app.fileInc.append(opt.string);
		elif opt.is_true('m', 'modify'):
			app.modifyIf += 1;
		elif opt.is_true('mforce'): # Modify whatsoever [3] -mmm, -mforce
			app.modifyIf = 3;
		elif opt.is_true('mhash'): # Modify if hash changed [2] -mm, --mhash
			app.modifyIf = 2;
		elif opt.is_true('murge'): # Modify if told by callbacks [1] -m, --murge
			app.modifyIf = 1;
	# Walker
		elif opt.is_string('name', 'g'):
			app.nameRE.append(dosGlob2RE(opt.string));
		elif opt.is_string('rname' 'e'):
			from re import compile;
			app.nameRE.append(compile(opt.string));
		elif opt.is_true('html'):
			app.modeHTML = opt.bool;
		elif opt.is_true('lxml'):
			app.useLXML = opt.bool;
		# else:
			# assert(False)
	# Call: on_xml_start (give chance to modify app)
	for x in app.plugIns:
		hasattr(x, 'on_xml_start') and x.on_xml_start(app);
	# Options
	#   ...
	# Globing
	if len(app.nameRE) < 1:
		from re import compile;
		app.nameRE.append(compile(app.modeHTML and r"^.+\.(x?html?)$" or r"^.+\.(?:xs(?:d|l)|xml)$"));
	#
	if app.useLXML:
		import sys, codecs
		try:
			from lxml import etree
			is_lxml=True
		except ImportError:
			try: # Python 2.5
				import xml.etree.cElementTree as etree
			except ImportError:
				try: # Python 2.5
					import xml.etree.ElementTree as etree
				except ImportError:
					try: # Normal cElementTree install
						import cElementTree as etree
					except ImportError:
						try: # Normal ElementTree install
							import elementtree.ElementTree as etree
						except ImportError:
							return logging.exception("Failed to import ElementTree from any known place");
			is_lxml=False
		def lxmlParse(f):
			kwargs = {}
			if is_lxml:
				kwargs['remove_blank_text'] = app.stripWS
				kwargs['remove_comments'] = app.stripComments
				kwargs['remove_pis'] = app.stripPIs
				kwargs['strip_cdata'] = app.stripCDatas
			if app.modeHTML:
				from lxml import html
				with open(f, "rb") as si:
					return html.parse(si)
			else:
				parser = etree.XMLParser(**kwargs)
			return etree.parse(open(f, "rb"), parser)
		def domHash(doc):
			h = HashSink()
			doc.write(h)
			return h.h.hexdigest();
		def domWrite(doc, out, enc, ctx):
			doc.write(out, xml_declaration=True, encoding=enc, pretty_print=ctx.savePretty)
		app.domEncoding = lambda doc: getDecl(app.filePath).get('encoding')
		app.domWrite = domWrite
		app.domParse = lxmlParse
		app.domHash = domHash
		app.domSinkFile = lambda f, enc: open(f, 'wb')
		app.domSinkOut = lambda enc: SinkRaw(sys.stdout, enc)
		app.domCall = 'on_xml_etree'
		app.domCallStart = 'on_xml_etree_start'
		app.domCallEnd = 'on_xml_etree_end'
		app.etree = etree
	else:
		import sys, codecs;
		app.domEncoding = lambda doc: getDecl(app.filePath).get('encoding')
		app.domHash = lambda doc: hashXMLNode(doc)
		app.domParse = lambda f: domLoadDoc(f, app)
		app.domSinkFile = lambda f, enc: codecs.open(f, 'wb', enc, 'xmlcharrefreplace')
		app.domSinkOut = lambda enc: Sink(sys.stdout, enc)
		app.domCall = 'on_xml_doc'
		app.domCallStart = 'on_xml_doc_start'
		app.domCallEnd = 'on_xml_doc_end'
		f = app.domWriter = DOMXMLWriter()
		if app.savePretty:
			f.tab = '  '
			f.newl = '\n'
		else:
			f.tab = None
			f.newl = None
		#~ app.domWrite = lambda doc, out, enc, ctx: doc.writexml(out, indent=ctx.useIndent, addindent=ctx.useTab, newl=ctx.useNL, encoding=enc)
		app.domWrite = domWriteDoc
	if app.checksModification:
		def wasModified():
			hash = app.domHash(app.domDoc)
			return hash and app.hashOfDOM and app.hashOfDOM != hash
		app.wasModified = wasModified
	# walk
	from os.path import isfile, isdir
	import os, sys
	_T = lambda _: _;
	if os.name == 'nt':
		if sys.hexversion < 0x03000000:
			_T = getattr(__import__('__builtin__'), 'unicode', None);
	for f in args:
		if f == '-':
			from sys import stdin;
			line = stdin.readline().strip();
			while line:
				onFile(line, app);
				line = stdin.readline().strip();
			continue
		f = _T(f)
		if isfile(f):
			onFile(f, app);
		elif isdir(f):
			f = fsinfo(f);
			f.depth = 0;
			f.rel = '';
			for f in walk_dir_pre(f):
				if f.isdir:
					f.walk = True;
					continue;
				x = f.name;
				for r in app.nameRE:
					if r.match(x):
						onFile(f.path, app);
						break;
		else:
			#TODO: URLs
			raise RuntimeError("File not found `%s'" % f);
	# Call: on_xml_end
	for x in app.plugIns:
		hasattr(x, 'on_xml_end')  and x.on_xml_end(app);
	# finish
	if len(TOT.__dict__):
		TOT.Kept = TOT.Total - TOT.Altered - TOT.Error;
	for k in gCounterMap:
		v = gCounterMap[k]
		len(v.__dict__) \
		and logging.info("%s: %s", k, ' '.join(('%s %d;' % (k, v) for (k, v) in v.__dict__.items())));

if __name__ == "__main__":
	from sys import exit
	exit(main(App()))
r"""
""";
