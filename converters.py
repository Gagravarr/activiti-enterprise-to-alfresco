# Various conversion helpers
class Output(object):
   def __init__(self, output_dir, filename, module_name):
      self.out = open("%s/%s" % (output_dir,filename),"w")
      self.module_name = module_name

   def begin(self, model_name, namespace_uri, namespace):
      pass

   def write(self, line):
      self.out.write(line)

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

   def complete(self):
      self.out.write("""
  </types>
</model>
""")
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

from constants import bpmn20_ns, activiti_ns, xml_namespaces

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
