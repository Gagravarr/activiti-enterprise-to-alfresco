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
 * context.xml - Context file to deploy the model and workflow, tweak the
                 names and paths within this for your project
 * model.xml   - Alfresco Model for the workflow form values
 * share.xml   - Share Custom Config with the form definitions in
 * FIXME.bpmn20.xml - Updated BPMN workflow definition

Tutorials and References
------------------------
Activiti Online:
http://activiti.alfresco.com/

Building an App with the Activiti Step Editor:
http://docs.alfresco.com/activiti/topics/app-step-editor.html

Tutorial on Activiti Workflows in Alfresco:
http://ecmarchitect.com/alfresco-developer-series-tutorials/workflow/tutorial/tutorial.html
