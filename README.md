# MHTifier
Un/packs an MHT (MHTML) archive into/from separate files, writing/reading them in directories to match their Content-Location.

Whole [story](http://decodecode.net/elitist/2013/01/mhtifier/) is in my devlog.

# Issues
1. Cleanest would've been to use stdin/out, but turned out inconvenient, annoying even, so added command line options.
2. Python's stdlib module's performance (premature optimization?):
	`email.message_from_bytes(mht.read()) # Parser is "conducive to incremental parsing of email messages, such as would be necessary when reading the text of an email message from a source that can block", so I guess it's more efficient to have it read stdin directly, rather than buffering.`
3. Encodings (ascii, UTF-8) and de/coding was painful, and probably still buggy.
4. base64 encoded binaries: my editor, Geany, suffocates, I think, when wrapping these long lines?
1. Verify index.html is present!?
1. A few un/Pythonisms, idioms,I guess.
