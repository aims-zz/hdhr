#!/usr/bin/env python
import readline
import sys
import os
import re

class Program:
   """This defines a 'program', basically a stream of a broadcast channel
   """
   def __init__(self):
      self.progid = 0
      self.name = None
      self.chan = None
      self.bcast = None

   def __str__(self):
      return "<%4s @%2s (#%2s): %s>" % (self.chan, self.bcast, self.progid, self.name)

   def __lt__(self, o):
      return self.chan < o.chan

class HDHomerunController:
   """Controls the hd homerun.
   """
   def __init__(self, deviceId, tunerId):
      self.deviceId = deviceId
      self.tunerId = tunerId
      self.scanning = None
      self.lock = None
      self.programs = []
      self.target = "none"
      self.prevChan = None
      self.currentChan = None

      self.re_scan = re.compile("us-bcast:(\d*)")
      self.re_program = re.compile("PROGRAM (\d*): (\d*\.\d*) (.*)")

   def parseLine(self, line):
      """Parses a single line from a scan file
      """
      m = self.re_scan.search(line);
      if m:
         self.scanning = m.group(1)
         return

      m = self.re_program.search(line)
      if m:
         p = Program()
         p.progid = int(m.group(1))
         p.name = m.group(3)
         p.chan = float(m.group(2))
         p.bcast = int(self.scanning)
         self.programs.append(p)

   def parseFile(self, filename):
      """Parses the output of hdhomerun_config scan
      """
      lines = []

      with open(filename) as f:
         lines = f.readlines()

      for line in lines:
         self.parseLine(line)

      self.programs.sort()

   def findProgramByChannel(self, chanid):
      """Just looks up a channel like 11.4 and returns the program object.
      """
      c = float(chanid)
      for p in self.programs:
         if p.chan == c:
            return p

   def showList(self):
      """Shows the list of channels we parsed from the input file.
      """
      for p in self.programs:
         print("Prog: %s" % str(p))
      print("Total %d programs" % len(self.programs))

   def changeProgram(self, chanid):
      """Changes the channel.
      """
      if self.target == "none" or not self.target:
         print("No target set.")
         return

      self.prevChan = self.currentChan
      self.currentChan = chanid

      p = self.findProgramByChannel(chanid)
      if not p:
         print("Invalid channel %s" % chanid)
         return

      os.system("hdhomerun_config %s set /tuner%s/channel %s" % (self.deviceId, self.tunerId, p.bcast))
      os.system("hdhomerun_config %s set /tuner%s/program %s" % (self.deviceId, self.tunerId, p.progid))
      os.system("hdhomerun_config %s set /tuner%s/target %s" % (self.deviceId, self.tunerId, self.target))
      print("Changed to %s" % (self.currentChan))

   def changeTarget(self, target):
      """Changes the target to receive video.
      """
      self.target = target
      print("Setting target to '%s'" % self.target)
      os.system("hdhomerun_config %s set /tuner%s/target %s" % (self.deviceId, self.tunerId, self.target))

   def prevChannel(self):
      """Changes back to the previously set channel.
      """
      if self.prevChan:
         self.changeProgram(self.prevChan)

   def status(self):
      """Shows the status of the tuner, stream, and what the script thinks the status is.
      """
      os.system("hdhomerun_config %s get /tuner%s/streaminfo" % (self.deviceId, self.tunerId))
      os.system("hdhomerun_config %s get /tuner%s/status" % (self.deviceId, self.tunerId))
      print("Channel .. %s" % self.currentChan)
      print("PrevCh ... %s" % self.prevChan)

   def showHelp(self):
      print("""
   list        - lists channels (cached)
   t <target>  - changes target IP for video
   ch <chan>   - changes to XX.YY channel
   prev        - previous channel
   status      - status

   help        - help
   q           - quits""")

   def interactive(self):
      while True:
         try:
            s = raw_input("HDHR> ")
         except EOFError, e:
            print("")
            break

         if s == "list":
            self.showList()

         elif s.startswith("t"):
            t = None
            try:
               t = s.split()[1]
            except:
               print("bad input")
               continue
            self.changeTarget(t)

         elif s.startswith("ch"):
            ch = None
            try:
               ch = s.split()[1]
            except:
               print("bad input")
               continue
            self.changeProgram(ch)

         elif s == "?" or s == "help" or s == "h":
            self.showHelp()

         elif s == "p" or s == "prev":
            self.prevChannel()

         elif s == "s" or s == "status":
            self.status()

         elif s == "quit" or s == "q":
            break

      # while True
      self.changeTarget("none")

if __name__ == '__main__':
   if len(sys.argv) < 4:
      print("usage: %s DEVICE_ID TUNER_ORDINAL SCAN_FILE" % (sys.argv[0]))
      sys.exit(1)

   device = sys.argv[1]
   tuner = sys.argv[2]
   filename = sys.argv[3]

   hdhr = HDHomerunController(device, tuner)
   hdhr.parseFile(filename)
   hdhr.interactive()

