#!/usr/bin/python
import os, sys
import json
import zipfile
import xml.etree.ElementTree as ET
from collections import OrderedDict
from constants import *
from converters import *

if len(sys.argv) < 4 or "--help" in sys.argv:
  print "Use:"
  print "   to-share.py <exported.bpmn> <exported-app.zip> <namespace prefix> [module name] [output dir]"
  print ""
  print " eg to-share.py exported.bpmn20.xml exported.zip sample-wf"
  sys.exit(1)

workflow = sys.argv[1]
app_zip  = sys.argv[2]
namespace = sys.argv[3]
module_name = sys.argv[4] if len(sys.argv) > 4 else "FIXME"
output_dir  = sys.argv[5] if len(sys.argv) > 5 else os.path.curdir

# Sanity check our options
with open(workflow, "r") as wf_file:
  wf_xml = wf_file.read()
if not wf_xml.startswith("<?xml version='1.0'") or not bpmn20_ns in wf_xml:
  print "Error - %s isn't a BPMN 2.0 workflow definition" % workflow
  sys.exit(1)

if os.path.exists(output_dir):
  print "Output files will be placed in '%s'" % output_dir
else:
  print "Error - desired output folder not found: %s" % output_dir
  print ""
  print "Please create or correct the path, and re-run"
  sys.exit(1)

if ":" in namespace or "_" in namespace:
  print "Namespace should be of the form namespace not name:space or name_space"
  print ""
  print "  eg sample-wf"
  print ""
  print "Which will map to sample-wf:Form1 sample-wf:Form2 etc"
  print ""
  print "Namespace should not contain a : as one will be added"
  print "Namespace should not contain a _ as that confuses the Share forms engine"
  sys.exit(1)

# Open the Activiti exported zip
app = zipfile.ZipFile(app_zip, "r")

# Setup for BPMN parsing
for prefix,ns in xml_namespaces.items():
   ET.register_namespace(prefix,ns)

# Look for Forms in the Workflow
tree = ET.parse(workflow)
wf = tree.getroot()
form_refs = wf.findall("**/[@{%s}formKey]" % activiti_ns)

if len(form_refs) == 0:
   print "No forms found in your workflow"
   print "The Workflow BPMN 2.0 XML file should be fine to be loaded into"
   print " your normal Alfresco instance and used as-is"

# Decide on the short namespace forms
namespace_sf = namespace + ":"
namespace_uri = "Activit_Exported_%s" % namespace
model_name = "%s:model" % namespace

# Check we only had one process
process_id = []
process_tag_name = "{%s}process" % bpmn20_ns
for elem in wf:
   if elem.tag == process_tag_name:
      process_id.append(elem.attrib["id"])
if len(process_id) == 1:
   process_id = process_id[0]
else:
   print "Expected 1 process definition in your BPMN file, but found %d" % (len(process_id))
   print "Only one process per file is supported"
   print "Found: %s" % " ".join(process_id)
   sys.exit(1)

# Start building out model and form config
model = ModelOutput(output_dir, module_name)
model.begin(model_name, namespace_uri, namespace)

context = ContextOutput(output_dir, module_name)
context.begin(model_name, namespace_uri, namespace)

share_config = ShareConfigOutput(output_dir, module_name)
share_config.begin(model_name, namespace_uri, namespace)

##########################################################################

def handle_fields(fields, share_form):
   for field in fields:
      # Is this a normal field, or a container with children?
      child_fields = get_child_fields(field)
      if child_fields:
         # Recurse, we don't care about container formatting at this time
         # TODO Track the containers into sets
         handle_fields(child_fields, share_form)
      else:
         # Handle the form field
         field_to_model(field, True)
         field_to_share(field)

def handle_outcomes(outcomes, form, share_form):
   if not outcomes:
      return
   if len(outcomes) == 1:
      outcome = outcomes[0]
      name = outcome.get("name")
      if not outcome.get("id") and name in transition_default_names:
         return
   # Fake it into a Field
   outcome_prop = "%sOutcome" % form.form_new_ref
   outcome_id = outcome_prop.split(":")[1]
   field = {"id":outcome_id, "name":"Outcome for Form %d" % form.form_num,
            "type":"text", "transition":True, "options":outcomes}
   # Have the Model and Share bits generated
   field_to_model(field, True)
   field_to_share(field)
   # Register it for BPMN Fixings
   OutcomeFixer.register_outcome(form.form_ref, outcome_prop)
   form.outcomes.append(outcome_prop)

def field_to_model(field, as_form):
   field_id, alf_id, name = build_field_ids(field, namespace)

   print " %s -> %s" % (field_id,name)

   # If it's an Aspect field, and we're currently working
   #  on a Form, then skip adding it to the model - done later
   if as_form and field.has_key("on-aspect"):
      print "    Via aspect %s" % field["on-aspect"].name
      return
   else:
      # Convert to Property or Assoc
      model.convert_field(field)

def field_to_share(field):
   share_form.convert_field(field)
   # TODO Use this to finish getting and handling the other options
   #print _field_to_json(field)

##########################################################################

# Finds the child fields of a form / container field
def get_child_fields(container):
   if isinstance(container,Form):
      return container.json["fields"]
   fields = []
   if container.get("fieldType","") == "ContainerRepresentation":
      for f in container["fields"]:
          if f in ("1","2","3","4"):
             for cf in container["fields"][f]:
                if cf:
                   fields.append(cf)
          else:
             print "Non-int field in fields '%s'" % f
             print json.dumps(field, sort_keys=True, indent=4, separators=(',', ': '))
   return fields
def get_all_child_fields(form):
   fields = []
   def do_field(field,fields):
      cf = get_child_fields(field)
      if cf:
         for f in cf:
            do_field(f, fields)
      else:
         fields.append(field)
   do_field(form, fields)
   return fields


# Load the forms into memory, so we can pre-process stuff
class Form(object):
   def __init__(self, form_num, form_elem):
      self.form_elem = form_elem
      self.form_num = form_num

      self.form_tag = form_elem.tag
      self.form_ref = form_elem.get("{%s}formKey" % activiti_ns)
      self.tag_name = form_elem.tag.replace("{%s}" % bpmn20_ns, "")
      self.form_id = form_elem.get("id","(n/a)")
      self.form_title = form_elem.attrib.get("name",None)
      self.aspects = []
      self.outcomes = []

   def update_form_id(self):
      self.form_new_ref = "%s:Form%d" % (namespace, self.form_num)
      self.form_elem.set("{%s}formKey" % activiti_ns, self.form_new_ref)

   def task_vars_to_execution(self):
      # List of Property IDs to copy over
      to_set = []
      # Any Custom Outcomes need doing
      to_set.extend( self.outcomes )
      # As do any writable aspect properties
      # TODO Filter out fields which are read-only on this form
      for aspect in self.aspects:
         for field in aspect.fields:
            to_set.append( build_field_ids(field, namespace)[1] )
      # Have the BPMN updated for these
      if to_set:
         TaskToExecutionFixer.fix(self.form_elem, to_set)

   def load_json(self):
      # Locate the JSON for it
      self.form_json_name = None
      for f in app.namelist():
         if f.startswith("form-models/") and f.endswith("-%s.json" % self.form_ref):
            self.form_json_name = f
      if self.form_json_name:
         print " - Reading from %s" % self.form_json_name
      else:
         print "Error - %s doesn't have a form-model for %s" % (app_zip, self.form_ref)
         sys.exit(1)
      # Read the JSON from the zip
      self.json = json.loads(app.read(self.form_json_name))
      # Newer Activiti exports put all the good bits in Editor JSON
      if self.json.has_key("editorJson"):
         self.json = self.json.get("editorJson")

forms = []
for form_num in range(len(form_refs)):
   # Build a wrapper around the form
   form = Form(form_num,form_refs[form_num])
   # Read the JSON from the zip
   form.load_json()
   # Record this completed form
   forms.append( form )
print ""

##########################################################################

## Detect forms with the same elements in them, and do those as an Aspect
# Work out which fields are used in multiple forms
form_fields = {}
for form in forms:
   fields = get_all_child_fields(form)
   for f in fields:
      field_id = f["id"]
      if not form_fields.has_key(field_id):
         form_fields[field_id] = {}
      form_fields[field_id][form] = f

class Aspect(object):
   def __init__(self, aspect_id, forms):
      self._build_name(aspect_id)
      self.aspect_id = aspect_id
      self.fields = []
      self.field_ids = []
      self.forms = forms
      for form in forms:
         form.aspects.append(self)
   def _build_name(self, aspect_id):
      if not type(aspect_id) in (str,unicode):
         aspect_id = "%d" % aspect_id
      self.base_name = "Aspect%s" % aspect_id
      self.name = "%s:%s" % (namespace, self.base_name)
   def add_field(self, field_id, field):
      # Record only the first instance of a field for model use
      if not field_id in self.field_ids:
         self.fields.append(field)
         self.field_ids.append(field_id)
      # Always nobble the defintion on the form
      field["on-aspect"] = self

# Group the fields by forms using them
aspects = []
_tmp_aspects = OrderedDict()
for field_id in form_fields.keys():
   field_forms = form_fields[field_id].keys()
   if len(field_forms) > 1:
      wanted_by = ",".join([f.form_id for f in field_forms])
      if not _tmp_aspects.has_key(wanted_by):
         aspect = Aspect(len(aspects), field_forms)
         _tmp_aspects[wanted_by] = aspect
         aspects.append(aspect)
      for form in field_forms:
         field = form_fields[field_id][form]
         _tmp_aspects[wanted_by].add_field(field_id, field)

# For the aspects with one field, try to give them a better name
for aspect in aspects:
   if len(aspect.fields) == 1:
      field_id = build_field_ids(aspect.fields[0], namespace)[0]
      aspect._build_name(field_id)

# Report what Aspects we've built
for wb, aspect in _tmp_aspects.items():
   print "Aspect %d needed by %d forms, with %d fields, called %s" % \
         (aspect.aspect_id, len(aspect.forms), len(aspect.fields), aspect.base_name)

##########################################################################

# Process the forms in turn
for form in forms:
   print ""
   print "Processing form %s for %s / %s" % (form.form_ref, form.tag_name, form.form_id)
   for aspect in form.aspects:
     print " Uses Aspect %s" % (aspect.name)

   # Update the form ID on the workflow
   form.update_form_id()
   form_new_ref = form.form_new_ref

   # Work out what type to make it
   alf_task_type, is_start_task = get_alfresco_task_types(form)

   # Prepare for the Share Config part
   share_form = ShareFormConfigOutput(share_config, process_id, form_new_ref, namespace)

   # Process as a type
   model.start_type(form)
   handle_fields(get_child_fields(form), share_form)
   handle_outcomes(form.json.get("outcomes",[]), form, share_form)
   model.end_type(form)

   # Do the Share Config conversion + output
   if is_start_task:
      share_form.write_out(True, True)
   share_form.write_out(is_start_task, False)

   # If the form has any writable aspect fields, or has custom outcomes,
   #  have those copied from the task to the execution scope
   form.task_vars_to_execution()

# Output the aspect definitions to the model
for aspect in aspects:
   print ""
   print "Processing aspect %s for %s" % (aspect.aspect_id, aspect.name)
   model.start_aspect(aspect.name)
   for field in aspect.fields:
      field_to_model(field, False)
   model.end_aspect()

##########################################################################

# Sort out things that Activiti Enterprise is happy with, but which
#  Activiti-in-Alfresco won't like
BPMNFixer.fix_all(wf)

# Output the updated workflow
updated_workflow = os.path.join(output_dir, "%s.bpmn20.xml" % module_name)
tree.write(updated_workflow, encoding="UTF-8", xml_declaration=True)

# Finish up
model.complete()
context.complete()
share_config.complete()

# Report as done
print ""
print "Conversion completed!"
print "Files generated are:"
for f in (model,context,share_config,updated_workflow):
   if hasattr(f,"outfile"):
      print "  %s" % f.outfile
   else:
      print "  %s" % f
