# Various conversion helpers
class Output(object):
   def __init__(self, output_dir, filename):
      self.out = open("%s/%s" % (output_dir,filename),"w")

   def begin(self, model_name, namespace_uri, namespace):
      pass

   def write(self, line):
      self.out.write(line)

   def complete(self):
      self.out.close()
      self.out = None

##########################################################################
class ModelOutput(Output):
   def __init__(self, output_dir):
      Output.__init__(self,output_dir,"model.xml")

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
