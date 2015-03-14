#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import codecs
import argparse
import re
from HTMLParser import HTMLParser

class Vulcanizer(HTMLParser):
	def __init__(self, output, strip, path):
		HTMLParser.__init__(self)
		self.__strip = strip
		self.__output = output
		self.__linkedData = u""
		self.__path = path
		self.__currentFileDir = None
		self.__inscript = False

	def process(self, documentPath):
		self.__currentFileDir = os.path.dirname(documentPath)
		with codecs.open(documentPath, encoding='utf-8', mode="r") as fh:
			# TODO: Read the file content by chunk to prevent memory consumption
			content = fh.read()
			self.feed(content)
	
	def __handleLink(self, href):
		linkPath = os.path.normpath(os.path.join(self.__currentFileDir, href))
		vulcanizer = Vulcanizer(self.__output, self.__strip, self.__path)
		vulcanizer.process(linkPath)
	
	def __handle_genericstart(self, tag, attrs):
		if tag == "link":
			a = dict(attrs)
			if a["rel"] == "import" and "href" in a:
				self.__handleLink(a["href"])
			return False
		else:
			self.__output.write("<%s" % tag)
			attrList = []
			for name, value in attrs:
				attrList.append("%s=\"%s\"" % (name, value))
			if len(attrList) > 0:
				self.__output.write(" %s" % " ".join(attrList))

		return True
	
	def handle_starttag(self, tag, attrs):
		if self.__handle_genericstart(tag, attrs):
			self.__output.write(">")
		if tag == "script":
			self.__inscript = True
	
	def handle_endtag(self, tag):
		if tag == "link":
			pass
		else:
			self.__output.write("</%s>" % tag)
		if tag == "script":
			self.__inscript = False
	
	def handle_startendtag(self, tag, attrs):
		if self.__handle_genericstart(tag, attrs):
			self.__output.write(" />")
	
	def handle_data(self, data):
		if self.__strip:
			if self.__inscript:
				data = data.replace("\n","")
				data = data.replace("\r","")
				data = re.sub("/\*.*\*/", "", data)
				data = re.sub(" +(?=(?:[^\"]*\"[^\"]*\")*[^\"]*$)", "", data)
				data = re.sub("\t+(?=(?:[^\"]*\"[^\"]*\")*[^\"]*$)", "", data)
			self.__output.write("%s" % data.strip())
		else:
			self.__output.write("%s" % data)
	
	def handle_entityref(self, name):
		self.__output.write("&%s;" % name)
	
	def handle_charref(self, name):
		self.__output.write("&%s;" % name)
	
	def handle_comment(self, data):
		pass
	
	def handle_decl(self, data):
		self.__output.write("<!%s>" % data)
	
	def handle_pi(self, data):
		self.__output.write("<!%s>" % data)
	
	def unknown_decl(self, data):
		self.__output.write("%s" % data)
	
def getArguments():
	parser = argparse.ArgumentParser(description='Concatenate a set of Web Components into one file')
	parser.add_argument("inputfiles", metavar="HTMLFILE", nargs=1, help="HTML file to process")
	parser.add_argument("-o", "--output", metavar="OUTPUT", nargs="?", help="Path to the output file. Standard output if not used")
	parser.add_argument("-s", "--strip", action="store_true", help="Remove comments and empty text nodes")
	parser.add_argument("-p", "--path", metavar="PATH", action="append", default=[], help="Path to search for relative path in import tag")
	parser.add_argument("-M", "--dependencies", action="store_true", help="Instead of outputting the vulcanized data, output relative path to imported document splitted by a new line")
	
	args = parser.parse_args()
	return args

def main():
	args = getArguments()
	
	for inputFile in args.inputfiles:
		if not os.path.exists(inputFile):
			print("Input file \"%s\" not found" % inputFile)
			return 1
	
	output = None
	if args.output != None:
		output = open(args.output, "w")
	else:
		output = sys.stdout
	
	for inputFile in args.inputfiles:
		vulcanizer = Vulcanizer(output, args.strip, args.path)
		vulcanizer.process(inputFile)

if __name__ == "__main__":
	main()
