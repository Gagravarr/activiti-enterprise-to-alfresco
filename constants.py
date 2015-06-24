# These are various constants and mappings we rely on

# Namespaces
bpmn20_ns = 'http://www.omg.org/spec/BPMN/20100524/MODEL'
activiti_ns = 'http://activiti.org/bpmn'

xml_namespaces = { 
  '':bpmn20_ns, 'activiti':activiti_ns,
  'bpmndi':'http://www.omg.org/spec/BPMN/20100524/DI',
  'omgdc':'http://www.omg.org/spec/DD/20100524/DC',
  'omgdi':'http://www.omg.org/spec/DD/20100524/DI',
  'xsi':'http://www.w3.org/2001/XMLSchema-instance',
  'xsd':'http://www.w3.org/2001/XMLSchema',
}

# Activiti tasks types as used by Alfresco One 
start_task = "bpm:startTask"

# Mappings from Activiti Online to Alfresco one models
model_types = { bpmn20_ns: {
   "startEvent": start_task,
   "userTask": "bpm:activitiOutcomeTask",
}}

# Mappings from Activiti Online form fields to Share ones
property_types = {
   "date": "d:date",
   "integer": "d:int",
   "text": "d:text",
   "multi-line-text": "d:text",
   "readonly-text": "d:text",
   "radio-buttons": "d:text",
   "dropdown": "d:text",
}
assoc_types = {
   "people": [False,False,"cm:person",False,False],
}
