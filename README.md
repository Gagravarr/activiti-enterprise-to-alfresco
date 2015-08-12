Activiti Enterprise to Alfresco Converter
-----------------------------------------

Converts Activiti Enterprise packages to be able to run on Alfresco One 
on-premise instances (Community and Enterprise)

Why Use This?
-------------
Alfresco One (Community and Enterprise), aka Alfresco on-premise, has a 
built-in copy of the Activiti workflow engine. You can build your own BPMN 2.0
workflows in any tool you like (such as the Activiti Designer), and then
deploy these to the repo. You then need to create a matching model, and define
some Share forms config to let your workflow play nicely in Share.

Recently, Alfresco Activiti Enterprise has launched, which is both a 
cloud-hosted and an on-premise version of the Activiti engine coupled with 
quite a nifty UI. Using this, it's possible for non-developers to easily
design their own workflows (with an advanced BPMN 2.0 editor/designer, and a
simpler step Editor), then create forms for them, which they can then deploy
and test. All of this can be done from your browser, by a non-developer,
in a quick way. It is possible to plug this into Alfresco One, but you
need to buy it, and it involves quite a few changes.

Alternately, you can use the online version at http://activiti.alfresco.com/
to prototype, then when your business users + you are happy with how it's
working there, export it + convert it + deploy in your on-premise Alfresco
repo.

How to use this
---------------
First, use http://activiti.alfresco.com/ to build your workflow and your 
forms for it. Test it there, make sure you're happy.

Next, export the Workflow, and export the App

Run this converter tool against the two, giving a name for the new on-premise
version, and have the converted BPMN 2.0 + model + Share forms config 
generated for you.

Tweak these as needed (eg naming), then deploy to your on-premise Alfresco!

Use detail
----------
to-share.py &lt;exported.bpmn> &lt;exported-app.zip> &lt;namespace prefix> [output dir]

Where:
 * *exported.bpmn* - BPMN workflow exported from Activiti
 * *exported-app.zip* - App definition zip exported from Activiti
 * *namespace prefix* - Prefix to use for the local version, eg sample-wf

This will generate in the output directory four files:
 * module-context.xml - Context file to deploy the model and workflow, 
                 tweak the names and paths within this for your project
 * model.xml   - Alfresco Model for the workflow form values
 * share.xml   - Share Custom Config with the form definitions in
 * FIXME.bpmn20.xml - Updated BPMN workflow definition

Deploy detail
-------------
After running the converter, review your output for sanity, and fix any errors 
/ warnings reported during the run. Next, rename your files to have sensible 
names for your use case, and edit the module name and BPMN file name in the
module context.

Copy the following to your Alfresco install:
 * *renamed FIXME.bpmn20.xml* -> *Alfresco classes*/alfresco/module/*mname*/*renamed*.bpmn20.xml
 * module-context.xml -> *Alfresco classes*/alfresco/module/*mname*/
 * model.xml -> *Alfresco classes*/alfresco/module/*mname*/

And to your Share install:
 * share.xml -> *Share classes*/alfresco/web-extension/share-config-custom.xml

Limitations
-----------
Currently, only simpler workflows and applications can be converted. You will
received warnings and errors for unsupported features.

Required fields, default values and multiple values are currently not
supported. Fields using those get converted into simple single value fields.

Activiti-online style Due Dates are not supported, and will be ignored.

At this time, column information in the form definition is discarded, and 
the generated Share configuration is simply created with a single column.

Tutorials and References
------------------------
Activiti Online:
http://activiti.alfresco.com/

Building an App with the Activiti Step Editor:
http://docs.alfresco.com/activiti/topics/app-step-editor.html

Tutorial on Activiti Workflows in Alfresco:
http://ecmarchitect.com/alfresco-developer-series-tutorials/workflow/tutorial/tutorial.html
