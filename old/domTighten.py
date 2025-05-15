def domCanTighten(cur):
	"""
perl -mHTML::Element -e "print qq[(] . join(',',map {qq['$_']} sort(keys(%HTML::Element::canTighten))) . qq[)]"
	"""
	return cur.nodeType in (cur.PROCESSING_INSTRUCTION_NODE, cur.COMMENT_NODE) or \
		cur.localName in ('address','applet','area','base','bgsound','blockquote','body','br','button','caption','center','col','colgroup','dd','del','dir','div','dl','dt','fieldset','form','frame','frameset','h1','h2','h3','h4','h5','h6','head','hr','html','iframe','ilayer','ins','isindex','label','legend','li','link','map','menu','meta','multicol','noframes','nolayer','noscript','object','ol','optgroup','option','p','param','script','style','table','tbody','td','textarea','tfoot','th','thead','title','tr','ul','~comment','~directive','~literal','~pi')
def htmlIsEmpty(cur):
	#~ perl -mHTML::Element -e "print qq[(] . join(',',map {qq['$_']} sort(keys(%HTML::Element::emptyElement))) . qq[)]"
	return cur.localName in ('area','base','basefont','bgsound','br','col','embed','frame','hr','img','input','isindex','link','meta','param','spacer','wbr','~comment','~declaration','~literal','~pi')

import re;
def domTighten(cur, pre = None):
	t = cur.nodeType
	if t in (cur.TEXT_NODE,):
		x = cur.data;
		if x:
			if cur.nextSibling and cur.previousSibling: # at the middle
				n = (domCanTighten(cur.previousSibling) and 1 or 0) | (domCanTighten(cur.nextSibling) and 2 or 0);
			elif cur.nextSibling: # at start
				n = (domCanTighten(cur.parentNode) and 1 or 0) | (domCanTighten(cur.nextSibling) and 2 or 0);
			elif cur.previousSibling: # at the end
				n = (domCanTighten(cur.previousSibling) and 1 or 0) | (domCanTighten(cur.parentNode) and 2 or 0);
			else: # one and only
				n = (domCanTighten(cur.parentNode) and 3 or 0);
			if n > 2: # 3
				x = re.sub(r'\s+', ' ', x).strip();
			elif n > 1: # 2
				x = re.sub(r'\s+', ' ', x).rstrip();
			elif n > 0: # 1
				x = re.sub(r'\s+', ' ', x).lstrip();
			elif not pre:
				x = re.sub(r'\s+', ' ', x);
		if x:
			cur.data = x;
		else:
			cur.parentNode.removeChild(cur);
	elif t == cur.DOCUMENT_NODE:
		domTighten(cur.documentElement)
	elif t != cur.ELEMENT_NODE:
		return;
	if cur.firstChild:
		cur.normalize()
		pre = pre or (cur.localName in ('pre', 'script', 'style', 'xmp', 'listing', 'plaintext', 'textarea'));
		mae = cur.lastChild;
		while mae:
			x = mae;
			(mae, t) = (x.previousSibling, x.nodeType)
			if t == cur.PROCESSING_INSTRUCTION_NODE:
				cur.removeChild(x);
			elif t == cur.COMMENT_NODE:
				(x.data in ('more', 'nextpage')) or cur.removeChild(x);
			else:
				domTighten(x, pre);
	else:
		if cur.localName in ('span', 'div'):
			cur.parentNode.removeChild(cur);
		elif cur.localName in ('a',):
			cur.appendChild(cur.ownerDocument.createTextNode(""));
		#~ elif cur.localName in ('br',):
			#~ pass;
