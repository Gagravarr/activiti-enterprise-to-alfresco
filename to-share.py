#!/usr/bin/python
import os, sys
import json
import zipfile
import xml.etree.ElementTree as ET

bpmn20_ns = 'http://www.omg.org/spec/BPMN/20100524/MODEL'
activiti_ns = 'http://activiti.org/bpmn'
model_types = { bpmn20_ns: {
   "startEvent": "bpm:startTask",
   "userTask": "bpm:activitiOutcomeTask",
}}
property_types = {
   "date": "d:date",
   "integer": "d:int",
   "text": "d:text",
   "multi-line-text": "d:text",
   "dropdown": "d:text",
}

if len(sys.argv) < 4 or "--help" in sys.argv:
  print "Use:"
  print "   to-share.py <exported.bpmn> <exported-app.zip> <namespace> [output dir]"
  print ""
  print " eg to-share.py exported.bpmn20.xml exported.zip sample:wf"
  sys.exit(1)

workflow = sys.argv[1]
app_zip  = sys.argv[2]
namespace = sys.argv[3]
output_dir = sys.argv[4] if len(sys.argv) > 4 else "."

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

# Decide on the short namespace form
namespace_sf = namespace.split(":")[1]
namespace_lf = namespace.replace(":","_")

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
model = open("%s/model.xml" % output_dir, "w")
model.write("""
<?xml version='1.0' encoding='UTF-8'?>
<model xmlns='http://www.alfresco.org/model/dictionary/1.0' name='%s'>
  <version>1.0</version>
  <imports>
    <import uri="http://www.alfresco.org/model/dictionary/1.0" prefix="d"/>
    <import uri="http://www.alfresco.org/model/system/1.0" prefix="sys"/>
    <import uri="http://www.alfresco.org/model/content/1.0" prefix="cm"/>
    <import uri="http://www.alfresco.org/model/site/1.0" prefix="st"/>
  </imports>
  <namespaces>
    <namespace uri="%s" prefix="%s"/>
  </namespaces>
  <types>
""" % (namespace, namespace_lf,namespace_sf))

share_config = open("%s/share.xml" % output_dir, "w")
share_config.write("""
<alfresco-config>
  <config evaluator="string-compare" condition="activiti$%s">
    <forms>
""" % (process_id))
# TODO Is it right to have the start task opened like this?

context = open("%s/context.xml" % output_dir, "w")
context.write("""
?xml version='1.0' encoding='UTF-8'?>
<!DOCTYPE beans PUBLIC '-//SPRING//DTD BEAN//EN' 'http://www.springframework.org/dtd/spring-beans.dtd'>
<beans>

  <bean parent="dictionaryModelBootstrap">
    <property name="models">
      <list>
        <!-- TODO Correct this to where you put model.xml -->
        <value>alfresco/module/FIXME/model.xml</value>
      </list>
    </property>
  </bean>

  <bean parent="workflowDeployer">
    <property name="workflowDefinitions">
      <list>
        <props>
          <prop key="engineId">activiti</prop>
          <!-- TODO Correct this to where you put the updated BPMN file -->
          <prop key="location">alfresco/module/FIXME/FIXME.bpmn20.xml</prop>
          <prop key="mimetype">text/xml</prop>
          <prop key="redeploy">false</prop>
        </props>
      </list>
    </property>
  </bean>
""")

# Process the forms
def get_alfresco_task_type(task_tag):
   if "{" in task_tag and "}" in task_tag:
      tag_ns = task_tag.split("{")[1].split("}")[0]
      tag_name = task_tag.split("}")[1]
      mt = model_types.get(tag_ns, None)
      if not mt:
         print "Error - no tag mappings found for namespace %s" % tag_ns
         print "Unable to process %s" % task_tag
         sys.exit(1)
      alf_type = mt.get(tag_name, None)
      if not alf_type:
         print "Error - no tag mappings found for tag %s" % tag_name
         print "Unable to process %s" % task_tag
         sys.exit(1)
      return alf_type
   print "Error - Activiti task with form but no namespace - %s" % task_tag
   sys.exit(1)

def process_fields(fields):
   for field in fields:
      if field.get("fieldType","") == "ContainerRepresentation":
         # Recurse, we don't care about container formatting at this time
         for f in field["fields"]:
             if f in ("1","2","3","4"):
                process_fields(field["fields"][f])
             else:
                print "Non-int field in fields '%s'" % f
                print json.dumps(field, sort_keys=True, indent=4, separators=(',', ': '))
      else:
         # Handle the form field
         print "%s -> %s" % (field["id"],field.get("name",None))

         alf_id = "%s%s" % (namespace, field["id"])

         ftype = field["type"]
         if not property_types.has_key(ftype):
            print "Warning - unhandled type %s" % ftype
            print json.dumps(field, sort_keys=True, indent=4, separators=(',', ': '))
            ftype = "text"
         alf_type = property_types[ftype]

         # TODO Handle required, read-only, default values, multiples etc
         if field.get("options",None):
            print " Warning: Options ignored!"

         model.write("         <property name=\"%s\">\n" % alf_id)
         if field.get("name",None):
            model.write("           <title>%s</title>\n" % field["name"])
         model.write("           <type>%s</type>\n" % alf_type)
         model.write("         </property>\n")

         # TODO output the Share "field-visibility" for this
         # TODO output the Share "appearance" for this, with name as label

         # TODO Handle it, for now just dump contents
         #print json.dumps(field, sort_keys=True, indent=4, separators=(',', ': '))

for form_num in range(len(form_refs)):
   form_elem = form_refs[form_num]
   form_ref = form_elem.get("{%s}formKey" % activiti_ns)
   form_new_ref = "%sForm%d" % (namespace, form_num)
   tag_name = form_elem.tag.replace("{%s}" % bpmn20_ns, "")
   print "Processing form %s for %s / %s" % (form_ref, tag_name, form_elem.get("id","(n/a)"))

   # Work out what type to make it
   alf_task_type = get_alfresco_task_type(form_elem.tag)
   alf_task_title = form_elem.attrib.get("name",None)

   # Locate the JSON for it
   form_json_name = None
   for f in app.namelist():
      if f.startswith("form-models/") and f.endswith("-%s.json" % form_ref):
         form_json_name = f
   if form_json_name:
      print " - Reading from %s" % form_json_name
   else:
      print "Error - %s doesn't have a form-model for %s" % (app_zip, form_ref)
      sys.exit(1)

   # Read the JSON from the zip
   form_json = json.loads(app.read(form_json_name))

   # Process as a type
   model.write("    <type name=\"%s\">\n" % form_new_ref)
   if alf_task_title:
      model.write("       <title>%s</title>\n" % alf_task_title)
   model.write("       <parent>%s</parent>\n" % alf_task_type)
   model.write("       <properties>\n")

   process_fields(form_json["fields"])

   model.write("       </properties>\n")
   model.write("    </type>\n")

   # Output the new workflow
   # TODO

# Finish up
model.write("""
  </types>
</model>
""")
model.close()
share_config.write("""
    </forms>
  </config>
</alfresco-config>
""")
share_config.close()
context.write("""
</beans>
""")
context.close()
