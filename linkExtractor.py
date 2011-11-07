#!/usr/local/bin/python
# -*- coding: utf-8 -*-
          
# ESTEEM PROJECT (GOOGLE CUSTOM COURSE SEARCH ENGINES) DELIVERABLE
## Tony Hirst, a.j.hirst, Dept of Communication and Systems

## A script to generate Google Custom Search Engine Annotations file
## from external pointing links contained within OU VLE course webpages

## This script starts to raise and explore some of the issues involved as we scrape links from across a course.
## For example:
### how should we handle duplicate links?
### are we indexing pages, domains, or both in the CSE?
### should different SA docs be allowed to map on to different tabs in the CSE? How might we manage this?
### should we try to remember where each link came from?
### do we want to use different weights in the CSE for different links? How might we determine such weights?
### how should we handle links that point to eg libezproxified DOIs?

## The script in part relies on conventions in markup that are used to express the standardised format of the T151 course model.
## In particular, study weeks contain topic explorations, each of which has a common structure that we draw on:
### - questions used to frame a topic exploration
### - resources organised by type to support the topic exploration

##FURTHER IDEAS
### Add links shared via t151 tag on delicious to the CSE in a 'Student Recommended' tab 
### Add in links shared via a Google Reader feed to the CSE

# DEPENDENCIES
## We're going to load files in from a course related directory
import os
## Quick hack approach - use lxml parser to parse SA XML files
from lxml import etree
## When we test URLs, we might as well be able to parse them comprehensively
from urlparse import urlparse
# We may find it handy to generate timestamps...
import time

#CONFIGURATION
## There's a little bit of config information we need

## The label of the custom search engine we want the annotations file to apply to
cselabel="_cse_bf8jg9spayc"

## The directory the course XML files are in (separate directory for each course for now) 
SA_XMLfiledir='data/'
## We can get copies of the XML versions of Structured Authoring documents
## that are rendered in the VLE by adding &content=1 to the end of the URL
## [via Colin Chambers]
## eg http://learn.open.ac.uk/mod/oucontent/view.php?id=526433&content=1

## Use an OU Logo to bolster the promoted links
OU_LOGO_URL='http://kmi.open.ac.uk/images/ou-logo.gif'

#BUILD A LIST OF EXTERNAL LINKS
# We may get the same link referenced in several places, so build up a list of unique links
# At the moment, I'll key the dict with the URL, but an MD5 hash may be more convenient?
# Would it also be worth defining a link class to structure the link data?
externalLinks={}

#Maintain a list of unique links we have seen, along with a list of link text descriptors for each unique link
def addExternalLink(linkslist,link):
	url = link.get('href')
	desc = link.text
	if url in linkslist:
		linkslist[url]['desc'].append(desc)
		# Rather than increment a counter explicitly, base the number of occurrences of the link on the number of link text descriptions we have captured. If we were using a class, we could use a method to return the link occurrence on this basis.
		linkslist[url]['count']=len(linkslist[url]['desc'])
	else:
		linkslist[url]={'count':1,'desc':[desc]}
	return linkslist

# UTILITIES

#lxml flatten routine - grab text from across subelements
#via http://stackoverflow.com/questions/5757201/help-or-advice-me-get-started-with-lxml/5899005#5899005
def flatten(el):           
    result = [ (el.text or "") ]
    for sel in el:
        result.append(flatten(sel))
        result.append(sel.tail or "")
    return "".join(result)

#Quick and dirty handler for saving XML trees as files
def xmlFileSave(fn,xml):
	# Output
	txt = etree.tostring(xml, pretty_print=True)
	#print txt
	fout=open(fn,'wb+')
	#fout.write('<?xml version="1.0" encoding="UTF-8" ?>\n')
	fout.write(txt)
	fout.close()


#GENERATE A FREEMIND MINDMAP FROM A SINGLE T151 SA DOCUMENT
## The structure of the T151 course lends itself to a mindmap/tree style visualisation
## Essentially what we are doing here is recreating an outline view of the course that was originally used in the course design phase
def freemindRoot(page):
	tree = etree.parse('/'.join([SA_XMLfiledir,page]))
	courseRoot = tree.getroot()
	mm=etree.Element("map")
	mm.set("version", "0.9.0")
	root=etree.SubElement(mm,"node")
	root.set("CREATED",str(int(time.time())))
	root.set("STYLE","fork")
	#We probably need to bear in mind escaping the text strings?
	#courseRoot: The course title is not represented consistently in the T151 SA docs, so we need to flatten it
	title=flatten(courseRoot.find('CourseTitle'))
	root.set("TEXT",title)
	
	#For each SA doc, we need to handle it separately
	for page in listing:
		print page
		#Week 0 and Week 10 are special cases and don't follow the standard teaching week layout
		if page!='t151Week0.xml' and page!='t151Week10.xml':
			tree = etree.parse('/'.join([SA_XMLfiledir,page]))
			courseRoot = tree.getroot()
			generateFreeMindLinksMapFromDoc(courseRoot,root)
	return mm

def generateFreeMindLinksMapFromDoc(courseRoot,root):

	weektitle=courseRoot.find('.//Unit/Session/Title')
	week=courseRoot.find('.//Unit/Session')
	
	mmweek=etree.SubElement(root,"node")
	mmweek.set("TEXT",flatten(weektitle))
	mmweek.set("FOLDED","true")
	print 'looking for topics'
	topics=week.findall('.//Section')
	#Weeks are generally split into two topic explorations per week.
	#Handle each topic exploration separately
	for topic in topics:
		print 'trying topics'
		title=flatten(topic.find('.//Title'))
		if title.startswith('Topic'):
			resources=etree.SubElement(mmweek,"node")
			resources.set("TEXT",title)
			resources.set("FOLDED","true")
			handleMMquestions(topic,resources)
			handleMMlinks(topic,resources)

# We might as well include the questions in the mindmap view, as they unpack nicely...
def handleMMquestions(topicRoot,resources):
	qsection = topicRoot.find(".//SubSection")
	title=flatten(qsection[0])
	if title.startswith('Questions'):
		currResource=etree.SubElement(resources,"node")
		currResource.set("TEXT","Questions")
		currResource.set("FOLDED","true")
		qqsection=qsection.find('NumberedList')
		print qqsection
		if qqsection!=None:
			for question in qqsection.iter('ListItem'):
				qResource=etree.SubElement(currResource,"node")
				qtext=flatten(question)
				qResource.set("TEXT",qtext)
	
def handleMMlinks(topicRoot,resources):
	#Find the resources section; we're relying on all sorts of conventions here so this is likely to be brittle
	resourceLists = topicRoot.findall(".//InternalSection")

	for rl in resourceLists:
		title=flatten(rl[0])
		print title
		currResource=etree.SubElement(resources,"node")
		currResource.set("TEXT",title)
		currResource.set("FOLDED","true")
		links=rl.findall('.//ListItem/a')
		for link in links:
			linkResource=etree.SubElement(currResource,"node")
			linkResource.set("LINK",link.get('href'))
			#Once again, the SA doc is a mess. Sometimes there's a font tag, sometimes there isn't
			linktext=flatten(link)
			linkResource.set("TEXT",linktext)


#ADD IN LINKS TO THE CSE FROM AN EXTERNAL FEED
def grabFeedLinks(feed):
	pass

#GENERATE THE GOOGLE CSE ANNOTATIONS FILE

## For each link in a list, add it to the annotations tree
def addLinksToAnnotationsXML(annotations,links,cselabel):
	for url in links:
		print 'Handling',url
		#We only want the external links
		netloc=urlparse(url)[1]
		print '.........',netloc
		# There is a variety of links off the open.ac.uk domain, including libezproxy links
		# Maybe need to consider ways of handling these? Eg for libezproxy, should we maybe try to get a public abstract
		# page for the corresponding article added to the CSE index?
		if netloc.find('open.ac.uk')<0:
			print '... and using it...'
			annotation = etree.SubElement(annotations, "Annotation")
			annotation.set("about", url)
			# We captured the number of times a link was mentioned, so could we potentially use that to refine the score?
			annotation.set("score", "1")
			label = etree.SubElement(annotation, "Label")
			label.set("name", cselabel)
			label = etree.SubElement(annotation, "Label")
			label.set("name", "t151_course_resource")
		else:
			print '... and ignoring it...'
	return annotations

def getDomains(links,domainList={}):
	for url in links:
		netloc=urlparse(url)[1]
		if netloc.find('open.ac.uk')<0:
			if netloc in domainList:
				domainList[netloc]['count']=domainList[netloc]['count']+1
			else:
				domainList[netloc]={'domain':netloc,'cseInclude':'http://'+netloc+'/*','count':1}
	return domainList


# GENERATE GOOGLE CSE PROMOTIONS FILE
## The scoping of Python functions caught me out here... I wonder how many times I fall foul of this elsewhere?
## http://stackoverflow.com/questions/959113/python-function-calls-are-bleeding-scope-stateful-failing-to-initialize-parame
def checkDesc(desc):
	if len(desc)>199:
		desc=desc[:195]+' ...'
	#This is flakey as anything? How do we handle Unicode so Google importer is kept happy?
	desc=desc.replace(u'‘',"'")
	desc=desc.replace(u'’',"'")
	desc=desc.replace(u"\u00A0"," ")
	return desc

def checkQueryTags(tags):
	while len(tags)>499:
		tags=tags[:tags.rfind(',')]
	return tags

def createGenericQueryTags(cc,item,tags=None):
	if tags is None: tags = []
	tags.append(item.lower())
	tags.append(cc.upper()+' '+item.lower())
	tags.append(cc.lower()+' '+item.lower())
	return tags

def createWeekQueryTags(cc,week,weektags=None):
	if weektags is None: weektags = []
	weektags=createGenericQueryTags(cc,week,weektags)
	return weektags
	
def createTopicQueryTags(cc,topic,topictags=None):
	if topictags is None: topictags = []	
	topictags=createGenericQueryTags(cc,topic,topictags)
	##This is dangerous, and relies on a convention of "Topic Exploration NX"
	topicparts=topic.split(' ')
	topictags=createGenericQueryTags(cc,topicparts[2],topictags)
	topictags=createGenericQueryTags(cc,'topic '+topicparts[2],topictags)
	topictags=createGenericQueryTags(cc,'topic'+topicparts[2],topictags)
	return topictags

def createQuestionQueryTags(cc,topic,qn,questiontags=None):
	if questiontags is None: questiontags = []
	topicID=topic.split(' ')[2]
	questiontags=createGenericQueryTags(cc,'topic '+topicID+' q'+str(qn),questiontags)
	return questiontags
	
def createPromotions(promotions,courseRoot,cselabel):
	##The Promotions file provides a set of promoted links that appear at the top of the search results listing for a particular search query
	## the aim is to try to aut-generate sensible cribs for students based on calendar and topic searches
	week=courseRoot.find('.//Unit/Session')
	cc=courseRoot.find('.//CourseCode').text
	##So what promotions might we add?
	##The first promotion just identifies what the weeks topics are about?
	promotion=etree.SubElement(promotions,"Promotion")
	promotion.set('image_url',OU_LOGO_URL)
	weektitle=flatten(courseRoot.find('.//Unit/Session/Title'))
	promotion.set('title',weektitle)
	promotion.set('id',cc+'_'+weektitle.replace(' ',''))
	qtags=checkQueryTags(','.join(createWeekQueryTags(cc,weektitle)))
	promotion.set('queries',qtags)
	#I'm really not sure what we can plausibly set as a URL here?
	promotion.set('url','http://www.open.ac.uk')
	topics=week.findall('.//Section')
	desc=''
	#Weeks are generally split into two topic explorations per week.
	#Summarise the week by the topics it includes
	for topic in topics:
		title=flatten(topic.find('.//Title'))
		## The original doc includes Unicode characters that don't seem to to play nicely...
		## There's probably a better way of handling this, but I'm just a hack it and see type of programmer!
		title=title.replace(u'–','-')
		if title.startswith('Topic'):
			desc=desc+title+' '
	desc=checkDesc(desc)
	promotion.set('description',desc)
	
	##The second promotion type briefly describes a given topic
	for topic in topics:
		title=flatten(topic.find('.//Title'))
		title=title.replace(u'–','')
		if title.startswith('Topic'):
			promotion=etree.SubElement(promotions,"Promotion")
			promotion.set('image_url',OU_LOGO_URL)
			##What URL should we set here?
			promotion.set('url','http://www.open.ac.uk')
			##Probably need to find a better way of parsing the topic number and title out...
			topictxt=' '.join(title.split(' ')[:3])
			print topictxt
			promotion.set('title',topictxt)
			promotion.set('id',cc+'_'+topictxt.replace(' ',''))
			#At the moment the desc is the theme of the explorations. Maybe also give a list of how many questions?
			desc=checkDesc(' '.join(title.split(' ')[3:]))
			promotion.set('description',desc)
			topicdesc=desc
			qtags=checkQueryTags(','.join(createTopicQueryTags(cc,topictxt)))
			promotion.set('queries',qtags)
			
			##The third promotion type identifies the first 196 chars of each question
			qsection = topic.find(".//SubSection")
			title=flatten(qsection[0])
			if title.startswith('Questions'):
				qqsection=qsection.find('NumberedList')
				if qqsection!=None:
					qn=0
					for question in qqsection.iter('ListItem'):
						qn=qn+1
						qpromotion=etree.SubElement(promotions,"Promotion")
						qpromotion.set('image_url',OU_LOGO_URL)
						##What URL should we set here?
						qpromotion.set('url','http://www.open.ac.uk')
						##Probably need to find a better way of parsing the topic number and title out...
						qpromotion.set('title',topictxt+' Question '+str(qn))
						qpromotion.set('id',cc+'_'+topictxt.replace(' ','')+'_'+str(qn))
						qtext=flatten(question)
						desc=checkDesc(qtext)
						qpromotion.set('description',desc)
						qtags=checkQueryTags(','.join(createQuestionQueryTags(cc,topictxt,qn)))
						qpromotion.set('queries',qtags)
					#if there are questions, update the topic description
					topicdesc=topicdesc+' ('+str(qn)+' questions)'
					promotion.set('description',checkDesc(topicdesc))
			
	'''
	id="t151_start" 
        queries="t151, T151, start, start t151, start T151, T151 start, t151 start, about, about t151, t151 about" 
        title="T151 Getting Started" 
        url="http://ouseful.open.ac.uk/T151"
        description="Welcome to T151. To start the course, read through the Getting Started guide then come back and enter: t151 topic1a"
        image_url="http://kmi.open.ac.uk/images/ou-logo.gif"
    '''
	


######################## DO THE BUSINESS....
## Create an XML tree for the Annotations
cseAnnotations = etree.Element("Annotations")

## Grab a listing of the SA files in the target directory
listing = os.listdir(SA_XMLfiledir)

print 'Got listing'
## For each file, parse it as an XML doc, grab the links, and add them to the annotations list
##TO DO - this really needs tidying into a function
for page in listing:
	print page
	tree = etree.parse('/'.join([SA_XMLfiledir,page]))
	root = tree.getroot()
	links = root.findall(".//a[@href]")
	for link in links:
		externalLinks=addExternalLink(externalLinks,link)
	
cseAnnotations = addLinksToAnnotationsXML(cseAnnotations,externalLinks,cselabel)

#There may be occasions where we want to add the domains?
domainsList=getDomains(externalLinks)
print domainsList

xmlFileSave('tmp/testAnnotations.xml',cseAnnotations)

# Freemind Mindmap generator
## I want to get a feel for the structure around the links, and a mindmap visualisation might help with this
## In addition, the mimdmap view may be a useful spinoff...
mm=freemindRoot('t151Week10.xml')

xmlFileSave('tmp/test_full.mm',mm)

##Promotions file generator
promotions=etree.Element("Promotions")
for page in listing:
	print page
	if page!='t151Week0.xml' and page!='t151Week10.xml':
		tree = etree.parse('/'.join([SA_XMLfiledir,page]))
		root = tree.getroot()
		createPromotions(promotions,root,cselabel)

xmlFileSave('tmp/test_promotions.xml',promotions)
