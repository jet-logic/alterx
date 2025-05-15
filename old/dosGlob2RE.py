def dosGlob2RE(s):
	import re;
	s = re.escape(s);
	s = s.replace(r"\*", '.*');
	s = s.replace(r"\?", '.');
	return re.compile(s, re.I);
