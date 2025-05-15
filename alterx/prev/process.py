import logging

from os.path import abspath


class Status:
    def __init__(self, app):
        self.app = app
        self.hash = self.data = None

    def modified(self, parent=None):
        h1 = self.hash
        if h1 is True:
            return True
        elif h1:
            h2 = app.hash_of(self.data)
            return h2 and h1 != h2 and h2


def on_file(f, app):
    total = app.total
    this = Status(app)
    this.path = f = abspath(f)
    # Load document
    O = None
    try:
        this.data = O = app.parse_file(f, app)
    except:
        total.Errors += 1
        return logging.exception("Failed to load %r", f)
    else:
        logging.info("XML: %s %s", (app and ("[#%d]" % total.Files) or "ERROR"), f)
    # Feed to plugins
    if app.checksModification:
        if app.modifyIf == 2:
            this.hash = mHash = app.hash_of(O)
        else:
            mHash = None
            this.hash = app.hash_of(O)
    else:
        this.hash = mHash = (app.modifyIf == 2) and app.hash_of(O)
    mUrge = None

    fn_call = getattr(app, "fn_call")
    if isinstance(fn_call, str):
        for x in app.plugIns:
            r = getattr(x, fn_call, None)
            if r and r(O, app, this):
                mUrge = True
                this.hash = True
                # call back says he modified it
    else:
        for x in app.plugIns:
            for f in fn_call:
                r = getattr(x, f, None)
                if r and r(O, app, this):
                    mUrge = True
                    this.hash = True
                    # call back says he modified it

    # Was modified?
    if mHash:  # (app.modifyIf == 2) Modify if hash changed
        mSave = not (app.hash_of(O) == mHash)
    else:
        mSave = mUrge or (app.modifyIf > 2)
    if not mSave:
        return None
    # Modified, Save it
    encoding = app.useEncoding or app.encoding_of(O, f)
    if app.dryRun is False:
        out = None
        if len(app.fileOut) < 1:  # []
            out = app.sink_file(this.path, encoding)
        elif (len(app.fileOut) == 1) and (app.fileOut[0] == "-"):  # ['-']
            out = app.sink_out(encoding)
        else:  # ['file1', ...]
            out = app.sink_file(app.fileOut.pop(0), encoding)
        app.dump(O, out, encoding, app)
        out.close()
    total.Altered += 1
    logging.warning(
        f'{app.id} Altered {app.dryRun is False and "!" or "?"} {encoding and (" [" + encoding + "]") or ""}',
    )
