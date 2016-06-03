import xml.etree.ElementTree as ET
from xml.sax.saxutils import escape
from constants import *

##########################################################################

# Various conversion helpers / base classes

class Output(object):
   def __init__(self, output_dir, filename, module_name):
      import os
      self.outfile = os.path.join(output_dir, filename)
      self.out = open(self.outfile,"w")
      self.module_name = module_name

   def begin(self, model_name, namespace_uri, namespace):
      pass

   def write(self, line):
      self.out.write( line.encode("UTF-8") )

   def complete(self):
      self.out.close()
      self.out = None

class BPMNFixer(object):
   fixers = []
   def __init__(self, tag, attr):
      BPMNFixer.fixers.append(self)
      self.attr = attr
      self.tag = tag
   def fix_for_tag(self, tag):
      pass
   def fix_for_attr(self, tag, attr_val):
      pass
   @staticmethod
   def fix_all(wf):
      for fixer in BPMNFixer.fixers:
         if fixer.tag:
            tags = wf.findall(".//%s" % fixer.tag)
            for tag in tags:
               fixer.fix_for_tag(tag)
         if fixer.attr:
            tags = wf.findall("**/[@%s]" % fixer.attr)
            for tag in tags:
               attr_val = tag.get(fixer.attr)
               fixer.fix_for_attr(tag, attr_val)
   @staticmethod
   def add_script(ext_elem_tag, script_type, script):
      # Add the appropriate listener
      if script_type == "start":
         listener = ET.SubElement(ext_elem_tag,"{%s}executionListener"%activiti_ns)
         listener.set("event","start")
         listener.set("class","org.alfresco.repo.workflow.activiti.listener.ScriptExecutionListener")
      else:
         listener = ET.SubElement(ext_elem_tag,"{%s}taskListener"%activiti_ns)
         listener.set("event",script_type)
         listener.set("class","org.alfresco.repo.workflow.activiti.tasklistener.ScriptTaskListener")
      # Add the real script
      fscript = ET.SubElement(listener,"{%s}field"%activiti_ns)
      fscript.set("name","script")
      fstring = ET.SubElement(fscript,"{%s}string"%activiti_ns)
      fstring.text = script

##########################################################################

class ModelOutput(Output):
   def __init__(self, output_dir, module_name):
      Output.__init__(self,output_dir,"model.xml", module_name)
      self.to_close = "types"

   def begin(self, model_name, namespace_uri, namespace):
      self.namespace = namespace
      self.out.write("""<?xml version='1.0' encoding='UTF-8'?>
<model xmlns='http://www.alfresco.org/model/dictionary/1.0' name='%s'>
  <version>1.0</version>
  <imports>
    <import uri="http://www.alfresco.org/model/dictionary/1.0" prefix="d"/>
    <import uri="http://www.alfresco.org/model/system/1.0" prefix="sys"/>
    <import uri="http://www.alfresco.org/model/content/1.0" prefix="cm"/>
    <import uri="http://www.alfresco.org/model/site/1.0" prefix="st"/>
    <import uri="http://www.alfresco.org/model/bpm/1.0" prefix="bpm" />
  </imports>
  <namespaces>
    <namespace uri="%s" prefix="%s"/>
  </namespaces>
  <types>
""" % (model_name, namespace_uri, namespace))

   def _start(self):
      self.aspects = []
      self.associations = []
      self.out.write("       <properties>\n")
   def _end(self):
      self.out.write("       </properties>\n")
      if self.aspects:
         self.out.write("       <mandatory-aspects>\n")
         for aspect in self.aspects:
            self.out.write("          <aspect>%s</aspect>\n" % aspect.name)
         self.out.write("       </mandatory-aspects>\n")
      if self.associations:
         self.out.write("       <associations>\n")
         for assoc in self.associations:
            self.out.write("         <association name=\"%s\">\n" % assoc[0])
            if assoc[1]:
               self.out.write("           <title>%s</title>\n" % escape(assoc[1]))
            self.out.write("           <source>\n")
            self.out.write("             <mandatory>%s</mandatory>\n" % str(assoc[2][0]).lower())
            self.out.write("             <many>%s</many>\n" % str(assoc[2][1]).lower())
            self.out.write("           </source>\n")
            self.out.write("           <target>\n")
            self.out.write("             <class>%s</class>\n" % str(assoc[2][2]).lower())
            self.out.write("             <mandatory>%s</mandatory>\n" % str(assoc[2][3]).lower())
            self.out.write("             <many>%s</many>\n" % str(assoc[2][4]).lower())
            self.out.write("           </target>\n")
            self.out.write("         </association>\n")
         self.out.write("       </associations>\n")

   def start_type(self, form):
      alf_task_type, is_start_task = get_alfresco_task_types(form)

      self.out.write("\n")
      self.out.write("    <type name=\"%s\">\n" % form.form_new_ref)
      if form.form_title:
         self.out.write("       <title>%s</title>\n" % escape(form.form_title))
      self.out.write("       <parent>%s</parent>\n" % alf_task_type)
      self._start()
      self.aspects = form.aspects

   def end_type(self, form):
      self._end()
      self.out.write("    </type>\n")

   def start_aspect(self, name):
      if self.to_close == "types":
         self.to_close = "aspects"
         self.out.write("""
  </types>

  <aspects>
""")
      self.out.write("\n")
      self.out.write("    <aspect name=\"%s\">\n" % name)
      self._start()
   def end_aspect(self):
      self._end()
      self.out.write("    </aspect>\n")

   def convert_field(self, field):
      field_id, alf_id, name = build_field_ids(field, self.namespace)
      ftype, alf_type, options, required = build_field_type(field)

      # TODO Handle default values, multiples etc
      if alf_type:
         self.write("         <property name=\"%s\">\n" % alf_id)
         if name:
            self.write("           <title>%s</title>\n" % escape(name))
         self.write("           <type>%s</type>\n" % alf_type)
         if ftype == "readonly-text":
            self.write("           <default>%s</default>\n" % escape( field.get("value","") ))
         if required:
            self.write("           <mandatory>true</mandatory>\n")
         if options:
            self.write("           <constraints>\n")
            self.write("             <constraint type=\"LIST\">\n")
            self.write("               <parameter name=\"allowedValues\"><list>\n")
            for opt in options:
               self.write("                 <value>%s</value>\n" % escape(opt["name"]))
            self.write("               </list></parameter>\n")
            self.write("             </constraint>\n")
            self.write("           </constraints>\n")
         self.write("         </property>\n")
      if assoc_types.has_key(ftype):
         self.associations.append((alf_id,name,assoc_types.get(ftype)))

   def complete(self):
      self.out.write("""
  </%s>
</model>
""" % (self.to_close))
      Output.complete(self)

class ContextOutput(Output):
   def __init__(self, output_dir, module_name):
      Output.__init__(self,output_dir,"module-context.xml", module_name)

   def begin(self, model_name, namespace_uri, namespace):
      self.out.write("""<?xml version='1.0' encoding='UTF-8'?>
<!DOCTYPE beans PUBLIC '-//SPRING//DTD BEAN//EN' 'http://www.springframework.org/dtd/spring-beans.dtd'>
<beans>

  <bean id="%sModelBootstrap" 
        parent="dictionaryModelBootstrap" 
        depends-on="dictionaryBootstrap">
    <property name="models">
      <list>
        <!-- TODO Correct this to where you put model.xml -->
        <value>alfresco/module/%s/model.xml</value>
      </list>
    </property>
  </bean>

  <bean id="%sWorkflowDeployer" 
        parent="workflowDeployer">
    <property name="workflowDefinitions">
      <list>
        <props>
          <prop key="engineId">activiti</prop>
          <!-- TODO Correct this to where you put the updated BPMN file -->
          <prop key="location">alfresco/module/%s/%s.bpmn20.xml</prop>
          <prop key="mimetype">text/xml</prop>
          <prop key="redeploy">false</prop>
        </props>
      </list>
    </property>
  </bean>
""" % (namespace, self.module_name, namespace, self.module_name, self.module_name))

   def complete(self):
      self.out.write("""
</beans>
""")
      Output.complete(self)

class ShareConfigOutput(Output):
   def __init__(self, output_dir, module_name):
      Output.__init__(self,output_dir,"share.xml", module_name)

   def begin(self, model_name, namespace_uri, namespace):
      self.out.write("<alfresco-config>\n")

   def complete(self):
      self.out.write("""
</alfresco-config>
""")
      Output.complete(self)

##########################################################################

class ShareFormConfigOutput(object):
   default_indent = "        "
   def __init__(self, share_config, process_id, form_ref, namespace):
      self.share_config = share_config
      self.process_id = process_id
      self.form_ref = form_ref
      self.namespace = namespace

      self.custom_transitions = []
      self.visabilities = []
      self.appearances = []

   def record_visibility(self, vis):
      self.visabilities.append(vis)
   def record_appearance(self, app):
      self.appearances.append(app)
   def record_custom_transition(self, field_id):
      self.custom_transitions.append(field_id)

   def convert_field(self, field):
      field_id, alf_id, name = build_field_ids(field, self.namespace)
      ftype, alf_type, options, required = build_field_type(field)

      # Record the Share "field-visibility" for this
      self.record_visibility(alf_id)

      # Record the appearance details
      appearance = "<field id=\"%s\"" % alf_id
      if name:
         appearance += " label=\"%s\"" % escape(name)
      if field.get("readOnly", False):
         appearance += " read-only=\"true\""
      appearance += ">\n"

      value = escape(field.get("value",None) or "")
      if ftype == "readonly-text":
          appearance += "  <control template=\"/org/alfresco/components/form/controls/readonly.ftl\">\n"
          appearance += "    <control-param name=\"value\">%s</control-param>\n" % value
          appearance += "  </control>\n"
      if ftype == "multi-line-text":
          appearance += "  <control template=\"/org/alfresco/components/form/controls/textarea.ftl\">\n"
          appearance += "    <control-param name=\"value\">%s</control-param>\n" % value
          appearance += "  </control>\n"
      if ftype in ("radio-buttons","dropdown") and options:
          appearance += "  <control template=\"/org/alfresco/components/form/controls/selectone.ftl\">\n"
          appearance += "    <control-param name=\"options\">%s</control-param>\n" % ",".join([ escape(o["name"]) for o in options])
          appearance += "  </control>\n"
      if field.get("transition", False):
          appearance += "  <control template=\"/org/alfresco/components/form/controls/workflow/activiti-transitions.ftl\" />\n"
          self.record_custom_transition(alf_id)

      appearance += "</field>\n"
      self.record_appearance(appearance)

   def write_out(self, is_start=False, as_start=False):
      share_config = self.share_config
      default_indent = ShareFormConfigOutput.default_indent

      if as_start:
         share_config.write("""
  <config evaluator="string-compare" condition="activiti$%s">
""" % (self.process_id))
      else:
         share_config.write("""
  <config evaluator="task-type" condition="%s">
""" % (self.form_ref))

      # TODO What about <form id="workflow-details"> for non-start tasks?
      share_config.write("    <forms>\n")
      share_config.write("      <form>\n")

      share_config.write(default_indent+"<field-visibility>\n")
      for vis in self.visabilities:
          # Convert for non-start as needed
          if not as_start and "bpm:assignee" == vis:
             vis = "taskOwner"
          # Custom transitions must come last
          if vis in self.custom_transitions:
             continue
          # Output
          share_config.write(default_indent+"  <show id=\"%s\" />\n" % vis)
      if not as_start:
          share_config.write(default_indent+"  <show id=\"%s\" />\n" % "bpm:taskId")
          share_config.write(default_indent+"  <show id=\"%s\" />\n" % "bpm:status")
      if not is_start and not self.custom_transitions:
          share_config.write(default_indent+"  <show id=\"%s\" />\n" % "transitions")
      for trnid in self.custom_transitions:
          share_config.write(default_indent+"  <show id=\"%s\" />\n" % trnid)
      share_config.write(default_indent+"</field-visibility>\n")

      share_config.write(default_indent+"<appearance>\n")
      for app in self.appearances:
         # Output as-is with indent
         for l in [x for x in app.split("\n") if x]:
            share_config.write("%s  %s\n" % (default_indent,l))
      if not is_start and not self.custom_transitions:
         share_config.write(default_indent+"  <field id=\"transitions\"/>\n")
      share_config.write(default_indent+"</appearance>\n")

      share_config.write("      </form>\n")
      share_config.write("    </forms>\n")
      share_config.write("  </config>\n")

##########################################################################

def get_alfresco_task_types(form):
   "Returns the Alfresco model type and Share form type for a given task"
   task_tag = form.form_tag
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
      # Is it a start task?
      is_start_task = False
      if alf_type == start_task:
         is_start_task = True
      return (alf_type, is_start_task)
   print "Error - Activiti task with form but no namespace - %s" % task_tag
   sys.exit(1)

def build_field_ids(field, namespace):
   field_id = field["id"]
   for c in (u"\u2019","&",",",".",":",";"):
      field_id = field_id.replace(c,"")
   alf_id = "%s:%s" % (namespace, field_id)
   name = field.get("name", None)
   return (field_id, alf_id, name)

def build_field_type(field):
   ftype = field["type"]

   # If type is "readonly", ensure the read only flag is properly set
   if ftype == "readonly":
      field["readOnly"] = True

   # Is it one where the type information is nested?
   if ftype in type_nested_in_params:
      ftype = field["params"]["field"]["type"]

   # Check how to convert
   if not property_types.has_key(ftype) and not assoc_types.has_key(ftype):
      print "Warning - unhandled type %s" % ftype
      print _field_to_json(field)
      ftype = "text"

   alf_type = property_types.get(ftype, None)
   required = field.get("required", False)
   options = field.get("options", None)

   return (ftype, alf_type, options, required)

def _field_to_json(field):
   # Exclude bits we added onto the field
   import json
   fieldsmpl = dict((k,v) for k,v in field.iteritems() if not "aspect" in k)
   return json.dumps(fieldsmpl, sort_keys=True, indent=4, separators=(',', ': '))

##########################################################################

class AssigneeFixer(BPMNFixer):
   def __init__(self):
      BPMNFixer.__init__(self,None,"{%s}assignee" % activiti_ns)
   def fix_for_attr(self, task, assignee):
      if assignee in ("${initiator}","$INITIATOR"):
         task.set(self.attr, "${initiator.properties.userName}")
AssigneeFixer()

class DueDateFixer(BPMNFixer):
   def __init__(self):
      BPMNFixer.__init__(self,None,"{%s}dueDate" % activiti_ns)

   def fix_for_attr(self, task, due_date):
      if "${taskDueDateBean" in due_date:
         tag = task.tag.replace("{%s}"%activiti_ns,"").replace("{%s}"%bpmn20_ns,"")
         print ""
         print "WARNING: Activiti-online only Due Date found"
         print "   %s" % due_date
         print "The due date for %s / %s will be removed" % (tag, task.get("id","n/a"))
         task.attrib.pop(self.attr)
DueDateFixer()

class ActivitiMailFixer(BPMNFixer):
   """
   Alfrecso doesn't override/customise the Activiti MailActivityBehavior.
   To avoid mailing issues, we need to re-write Activiti mail service tasks
    into Alfresco mail actions
   """
   type_attr = "{%s}type"%activiti_ns
   field_mappings = {"to":"to","from":"from","subject":"subject","text":"text"}
   defaults = {"subject":"Activiti Workflow Task"}
   def __init__(self):
      BPMNFixer.__init__(self,"{%s}serviceTask"%bpmn20_ns,None)
   def fix_for_tag(self, task):
      if not task.get(ActivitiMailFixer.type_attr) == "mail":
         return
      extension = task.findall("{%s}extensionElements"%bpmn20_ns)[0]

      # Change it to a script task
      task.tag = "{%s}scriptTask"%bpmn20_ns
      task.set("scriptFormat","javascript")
      task.attrib.pop(ActivitiMailFixer.type_attr)

      # Build the script for mailing, and remove the Activiti fields
      script = "var mail = actions.create('mail');\n"
      done_fields = []
      for field in extension.findall("{%s}field" % activiti_ns):
         ftype = field.get("name")
         done_fields.append("field")
         if ActivitiMailFixer.field_mappings.has_key(ftype):
            alftype = ActivitiMailFixer.field_mappings[ftype]
            value = field.findall("{%s}string"%activiti_ns)[0].text
            script += "mail.parameters.%s = '%s';\n" % (alftype,value)
         else:
            print ""
            print "WARNING: Unknown Activiti-online mail field found"
            print "   %s" % exp
         extension.remove(field)
      for req_field, value in ActivitiMailFixer.defaults.items():
         if not req_field in done_fields:
            script += "mail.parameters.%s = '%s';\n" % (req_field, value)
      script += "mail.execute(bpm_package);\n"

      # Add the mailing script to the BPMN
      BPMNFixer.add_script(extension, "start", script)
      # Add a dummy script tag in the "wrong" place
      emptyscript = ET.SubElement(task, "{%s}script"%bpmn20_ns)
      emptyscript.text = "// No script here, run via an Execution listener"
ActivitiMailFixer()

class OutcomeFixer(BPMNFixer):
   outcomes = {}
   def __init__(self):
      BPMNFixer.__init__(self,"{%s}conditionExpression"%bpmn20_ns,None)

   @classmethod
   def register_outcome(cls, form_ref, outcome_prop):
      cls.outcomes[form_ref] = outcome_prop

   def fix_for_tag(self, tag):
      otype = tag.get("{%s}type" % xsi_ns)
      if otype == "tFormalExpression":
         exp = tag.text
         for form_id,alf_prop in OutcomeFixer.outcomes.items():
            aoe = "${form" + form_id + "outcome"
            if exp.startswith(aoe):
               act_prop = alf_prop.replace(":","_")
               repl = exp.replace(aoe, "${%s"%act_prop)
               tag.text = repl
               return
         print ""
         print "WARNING: Activiti-online only sequence condition found"
         print "   %s" % exp
OutcomeFixer()

class TaskToExecutionFixer(object):
   """
   Annoyingly, in most cases, Activiti under Alfresco won't make the
   task object available when scripts and expressions run
   So, for those we know will need it, explicitly copy the values from
   the task scope to the execution scope, so they can be used
   """
   extensionElements = "{%s}extensionElements"%bpmn20_ns
   @classmethod
   def fix(cls, task_tag, property_ids):
      # Build the script
      script = "\n"
      for alf_prop in property_ids:
         act_prop = alf_prop.replace(":","_")
         script += "execution.setVariable('%s', task.getVariable('%s'));\n" % \
                   (act_prop, act_prop)

      # Add the extension element if needed
      ee = task_tag.findall(cls.extensionElements)
      if ee:
         extension = ee[0]
      else:
         extension = ET.SubElement(task_tag, cls.extensionElements)

      # Work out the script type
      script_type = "complete"
      if task_tag.tag == start_task:
         script_type = "start"

      # Add the script
      BPMNFixer.add_script(extension, script_type, script)
