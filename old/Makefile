NAME=alterx

q1: .build/alterx.src

.build:
	mkdir .build

.build/alterx.src: .build alterx.*.py
	scrpp -I. -Iop -I.../_inc/python alterx.src.py | python  -c "import os,sys; a=os.fdopen(0,'Ub').read(); len(a) > 0 and open(sys.argv[1],'wb',16777216).write(a);" $@


#( pushd /mnt/META/wrx/python/alterx ; make q1 )
#mee --cd K:\wrx\python\alterx nmake q1 && alterx --stripws -h --no-pretty
