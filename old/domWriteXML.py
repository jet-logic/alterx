def domWriteData(out, data):
    if data:
        data = data.replace("&", "&amp;").replace("<", "&lt;").replace("\"", "&quot;").replace(">", "&gt;")
        out.write(data)

def domLastTightenable(cur):
	return domCanTighten(cur.previousSibling) if cur.previousSibling else domCanTighten(cur.parentNode)

def domWritewXML(ctx, cur, out, pre = False, depth = 0):
	#~ return cur.writexml(out)
	t = cur.nodeType
	depth2 = depth + 1
	if cur.ELEMENT_NODE == t:
		thisTightenable = domCanTighten(cur);
		if thisTightenable and (not pre) and domLastTightenable(cur):
			out.write(ctx.newl), out.write(ctx.tab * depth)
		out.write("<" + cur.tagName)
		attrs = cur._get_attributes()
		a_names = attrs.keys()
		a_names.sort()
		for a_name in a_names:
			out.write(" %s=\"" % a_name)
			domWriteData(out, attrs[a_name].value)
			out.write("\"")
		if cur.childNodes:
			out.write(">")
			pre2 = pre or (cur.localName in ('pre', 'script', 'style',  'xmp', 'listing', 'plaintext'));
			for node in cur.childNodes:
				domWritewXML(ctx, node, out, pre2, depth2)
			if pre2:
				pass
			elif thisTightenable and (not pre) and (cur.lastChild and domCanTighten(cur.lastChild)):
				out.write(ctx.newl), out.write(ctx.tab * depth)
			out.write("</%s>" % (cur.tagName,))
		else:
			out.write("/>")
	elif cur.TEXT_NODE == t:
		x = cur.data;
		if pre:
			return domWriteData(out, x)
		if domLastTightenable(cur):
			domWriteData(out, x)
		else:
			domWriteData(out, x)
	elif cur.DOCUMENT_NODE == t:
		out.write("<?xml")
		for t in (('version', ctx.version), ('encoding', ctx.encoding), ('standalone', ctx.standalone)):
			t[1] and out.write(' %s="%s"' % t)
		out.write("?>")
		out.write(ctx.newl or "\n")
		for node in cur.childNodes:
			domWritewXML(ctx, node, out, pre, depth) # NOTE: not using depth2
		ctx.newl and out.write(ctx.newl)
	elif cur.CDATA_SECTION_NODE == t:
		x = cur.data;
		if x.find("]]>") >= 0: raise ValueError("']]>' not allowed in a CDATA section")
		out.write("<![CDATA[%s]]>" % x)
	elif cur.COMMENT_NODE == t:
		if (not pre) and domLastTightenable(cur):
			out.write(ctx.newl), out.write(ctx.tab * depth)
		x = cur.data;
		if "--" in x: raise ValueError("'--' is not allowed in a comment node")
		out.write("<!--%s-->" % (x,))
	elif cur.PROCESSING_INSTRUCTION_NODE == t:
		if (not pre) and domLastTightenable(cur):
			out.write(ctx.newl), out.write(ctx.tab * depth)
		out.write("<?%s %s?>" % (cur.target, cur.data))
	else:
		assert(0)

class DOMXMLWriter(object):
	#~ __slots__ = ('tab', 'newl', 'encoding', 'standalone', 'version')
	version = '1.0'
	standalone = 'yes'
	encoding = 'UTF-8'
	tab = '\t'
	newl = '\n'
	def writexml(self, out, cur):
		domWritewXML(self, cur, out, not (self.tab or self.newl))
