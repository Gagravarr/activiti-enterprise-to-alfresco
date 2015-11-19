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
            tags = wf.findall("**/%s" % fixer.tag)
            for tag in tags:
               fixer.fix_for_tag(tag)
         if fixer.attr:
            tags = wf.findall("**/[@%s]" % fixer.attr)
            for tag in tags:
               attr_val = tag.get(fixer.attr)
               fixer.fix_for_attr(tag, attr_val)

##########################################################################

class ModelOutput(Output):
   def __init__(self, output_dir, module_name):
      Output.__init__(self,output_dir,"model.xml", module_name)
      self.to_close = "types"

   def begin(self, model_name, namespace_uri, namespace):
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
         for aspect in form.aspects:
            self.out.write("          <aspect>%s</aspect>\n" % aspect)
         self.out.write("       </mandatory-aspects>\n")
      if self.associations:
         self.out.write("       <associations>\n")
         for assoc in self.associations:
            self.out.write("         <association name=\"%s\">\n" % assoc[0])
            if assoc[1]:
               self.out.write("           <title>%s</title>\n" % assoc[1])
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
         self.out.write("       <title>%s</title>\n" % form.form_title)
      self.out.write("       <parent>%s</parent>\n" % alf_task_type)
      self._start()

   def end_type(self, form):
      self._end()
      self.out.write("    </type>\n")

   def start_aspect(self, todo):
      if self.to_close == "types":
         self.to_close = "aspects"
         self.out.write("""
  </types>

  <aspects>
""")
      self.out.write("\n")
      self.out.write("    <aspect name=\"%s\">\n" % "TODO")
      self._start()
   def end_aspect(self, todo):
      self._end()
      self.out.write("    </aspect>\n")

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
   def __init__(self, share_config, process_id, form_ref):
      self.share_config = share_config
      self.process_id = process_id
      self.form_ref = form_ref

      self.visabilities = []
      self.appearances = []

   def record_visibility(self, vis):
      self.visabilities.append(vis)
   def record_appearance(self, app):
      self.appearances.append(app)

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
          # Output
          share_config.write(default_indent+"  <show id=\"%s\" />\n" % vis)
      if not as_start:
          share_config.write(default_indent+"  <show id=\"%s\" />\n" % "bpm:taskId")
          share_config.write(default_indent+"  <show id=\"%s\" />\n" % "bpm:status")
      if not is_start:
          share_config.write(default_indent+"  <show id=\"%s\" />\n" % "transitions")
      share_config.write(default_indent+"</field-visibility>\n")

      share_config.write(default_indent+"<appearance>\n")
      for app in self.appearances:
         # Output as-is with indent
         for l in [x for x in app.split("\n") if x]:
            share_config.write("%s  %s\n" % (default_indent,l))
      if not is_start:
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

##########################################################################

class AssigneeFixer(BPMNFixer):
   def __init__(self):
      BPMNFixer.__init__(self,None,"{%s}assignee" % activiti_ns)
   def fix_for_attr(self, task, assignee):
      if "${initiator}" == assignee:
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
