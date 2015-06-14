#!/usr/bin/python
import os, sys
import json
import zipfile
import xml.etree.ElementTree as ET

bpmn20_ns = 'http://www.omg.org/spec/BPMN/20100524/MODEL'
activiti_ns = 'http://activiti.org/bpmn'

if len(sys.argv) < 4 or "--help" in sys.argv:
  print "Use:"
  print "   to-share.py <exported.bpmn> <exported-app.zip> <namespace>"
  print ""
  print " eg to-share.py exported.bpmn20.xml exported.zip sample:wf"
  sys.exit(1)

workflow = sys.argv[1]
app_zip  = sys.argv[2]
namespace = sys.argv[3]

# Sanity check our options
with open(workflow, "r") as wf_file:
  wf_xml = wf_file.read()
if not wf_xml.startswith("<?xml version='1.0'") or not \
    "http://www.omg.org/spec/BPMN/20100524/MODEL" in wf_xml:
  print "Error - %s isn't a BPMN 2.0 workflow definition" % workflow
  sys.exit(1)

if not ":" in namespace:
  print "Namespace should be of the form namespace:prefix"
  print ""
  print "  eg sample:wf"
  print ""
  print "Which will map to sample:wfForm1 samplewfForm2 etc"
  sys.exit(1)

app = zipfile.ZipFile(app_zip, "r")

# Look for Forms in the Workflow
wf = ET.fromstring(wf_xml)
form_refs = wf.findall("**/[@{%s}formKey]" % activiti_ns)

if len(form_refs) == 0:
   print "No forms found in your workflow"
   print "The Workflow BPMN 2.0 XML file should be fine to be loaded into"
   print " your normal Alfresco instance and used as-is"

for form_elem in form_refs:
   form_ref = form_elem.get("{%s}formKey" % activiti_ns)
   tag_name = form_elem.tag.replace("{%s}" % bpmn20_ns, "")
   print "Processing form %s for %s / %s" % (form_ref, tag_name, form_elem.get("id","(n/a)"))

   form_json_name = None
   for f in app.namelist():
      if f.startswith("form-models/") and f.endswith("-%s.json" % form_ref):
         form_json_name = f
   if form_json_name:
      print " - Reading from %s" % form_json_name
   else:
      print "Error - %s doesn't have a form-model for %s" % (app_zip, form_ref)
      sys.exit(1)

   form_json = json.json(app.read(form_json_name))
   print form_json
