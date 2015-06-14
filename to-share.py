#!/usr/bin/python
import os, sys

if len(sys.argv) < 4 or "--help" in sys.argv:
  print "Use:"
  print "   to-share.py <exported.bpmn> <exported-app.zip> <namespace>"
  print ""
  print " eg to-share.py exported.bpmn20.xml exported.zip sample:wf"
  sys.exit(1)
