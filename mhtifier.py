#!/usr/bin/env python3
# Encoding: UTF-8
"""mhtifier.py
Un/packs an MHT "archive" into/from separate files, writing/reading them in directories to match their Content-Location.

Uses part's Content-Location to name paths, or index.html for the root HTML.
Content types will be assigned according to registry of MIME types mapping to file name extensions.

History:
* 2013-01-11: renamed mhtifier.
* 2013-01-10: created mht2fs.py, and... done.
"""

# Standard library modules do the heavy lifting. Ours is all simple stuff.
import base64
import email, email.message
import mimetypes
import os
import quopri
import sys
import argparse

# Just do it.
def main():
	"""Convert MHT file given as command line argument (or stdin?) to files and directories in the current directory.

	Usage:
		cd foo-unpacked/
		mht2fs.py ../foo.mht
	"""
	parser = argparse.ArgumentParser(description="Extract MHT archive into new directory.")
	parser.add_argument("mht", metavar="MHT", help='path to MHT file, use "-" for stdin/stdout.')
	parser.add_argument("d", metavar="DIR", help="directory to create to store parts in, or read them from.") #??? How to make optional, default to current dir?
	parser.add_argument("-p", "--pack", action="store_true", help="pack file under DIR into an MHT.")
	parser.add_argument("-u", "--unpack", action="store_true", help="unpack MHT into a new DIR.")
	parser.add_argument("-v", "--verbose", action="store_true")
	parser.add_argument("-q", "--quiet", action="store_true")
	args = parser.parse_args() # --help is built-in.

	# Validate command line.
	if args.pack == args.unpack:
		sys.stderr.write("Invalid: must specify one action, either --pack or --unpack.\n")
		sys.exit(-1)

	# File name or stdin/stdout?
	if args.mht == "-":
		mht = sys.stdout if args.pack else sys.stdin.buffer
	else:
		if args.pack and os.path.exists(args.mht):
			# Refuse to overwrite MHT file.
			sys.stderr.write("Error: MHT file exists, won't overwrite.\n")
			sys.exit(-2)
		mht = open(args.mht, "wb" if args.pack else "rb")

	# New directory?
	if args.unpack:
		os.mkdir(args.d)

	# Change directory so paths (content-location) are relative to index.html.
	os.chdir(args.d)

	# Un/pack?
	if args.unpack:
		if not args.quiet:
			sys.stderr.write("Unpacking...\n")

		# Read entire MHT archive -- it's a multipart(/related) message.
		a = email.message_from_bytes(mht.read()) # Parser is "conducive to incremental parsing of email messages, such as would be necessary when reading the text of an email message from a source that can block", so I guess it's more efficient to have it read stdin directly, rather than buffering.				

		parts = a.get_payload() # Multiple parts, usually?
		if not type(parts) is list:
			parts = [a] # Single 'str' part, so convert to list.
                		                                                    
		# Save all parts to files.
		for p in parts: # walk() for a tree, but I'm guessing MHT is never nested?
			#??? cs = p.get_charset() # Expecting "utf-8" for root HTML, None for all other parts.						
			ct = p.get_content_type() # String coerced to lower case of the form maintype/subtype, else get_default_type().			
			fp = p.get("content-location") or "index.html" # File path. Expecting root HTML is only part with no location.

			if args.verbose:
				sys.stderr.write("Writing %s to %s, %d bytes...\n" % (ct, fp, len(p.get_payload())))

			# Create directories as necessary.
			if os.path.dirname(fp):
				os.makedirs(os.path.dirname(fp), exist_ok=True)

			# Save part's body to a file.
			open(fp, "wb").write(p.get_payload(decode=True))

		if not args.quiet:
			sys.stderr.write("Done.\nUnpacked %d files.\n" % (len(parts)))

	else:
		if not args.quiet:
			sys.stderr.write("Packing...\n")

		# Create archive as multipart message.
		a = email.message.Message()
		a["MIME-Version"] = "1.0"
		a.add_header("Content-Type", "multipart/related", type="text/html")

		# Walk current directory.
		for (root, _, files) in os.walk("."):
			# Create message part from each file and attach them to archive.
			for f in files:
				p = os.path.join(root, f).lstrip("./")
				m = email.message.Message()
				# Encode and set type of part.
				t = mimetypes.guess_type(f)[0]
				if t:
					m["Content-Type"] = t

				if args.verbose:
					sys.stderr.write("Reading %s as %s...\n" % (p, t))

				if t and t.startswith("text/"):
					m["Content-Transfer-Encoding"] = "quoted-printable"
					m.set_payload(quopri.encodestring(open(p, "rt").read().encode("utf-8")).decode("ascii")) #??? WTF?
				else:
					m["Content-Transfer-Encoding"] = "base64"
					m.set_payload(base64.b64encode(open(p, "rb").read()).decode("ascii"))
					#??? My editor, Geany, suffocates, I think, when needs to wrap these long lines?

				# Only set charset for index.html to UTF-8, and no location.
				if f == "index.html":
					m.add_header("Content-Type", "text/html", charset="utf-8")
					#??? m.set_charset("utf-8")
				else:
					m["Content-Location"] = p
				a.attach(m)

		# Write MHT file.
		#??? verify index.html is present!?
		mht.write(bytes(a.as_string(unixfrom=False), "utf-8")) # Not an mbox file, so we don't need to mangle "From " lines, I guess?

		if not args.quiet:
			sys.stderr.write("Done.\nPacked %d files.\n" % (len(a.get_payload())))

if __name__ == "__main__":
	main() # Kindda useless if we're not using doctest or anything?
