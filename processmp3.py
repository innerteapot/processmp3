#!/usr/bin/python
#
# Process MP3s - version 1.2
# by Joel Sutton <joel@crystaldreamsmusic.net>
#
# This script scans a given directory for flac or mp3 tracks, checks their
# encoded bit rate and transcodes them if necessary. Original files are moved to
# the specified archive directory.
#
# NB: lame and flac are required for this script to run
#

import commands
import glob
from hsaudiotag import auto
import os
import re
import shutil
import sys

class Track(object):
    """Object for storing data about a track"""
    def parse(self, f):
      """Examine the absolute file name given and populate object"""
      self.full_path    = f
      (head, tail)      = os.path.split(f)
      self.file         = tail
      self.path         = head

      # Example:
      #   Podcast - Dream Time - Still Stream - podcast - 2012 - 23-Dream Time Episode 023.mp3
      #
      r = re.search(r'(.+) - (.+) - (.+) - (.+) - (.+) - (\d+-.+\..+)', self.file)

      if r:
          self.artist       = r.group(1)
          self.album        = r.group(2)
          self.label        = r.group(3)
          self.ref          = r.group(4)
          self.year         = r.group(5)
          self.track        = r.group(6)

          return True
      else:
          r = re.search(r'(.+)\.(.+)', self.file)

          if r:
              self.track     = r.group(1)
              self.extension = r.group(2)
              return True
          else:
              return False

class TrackMP3(Track):
    """mp3 specific sub-class"""
    def parse(self, f):
        Track.parse(self, f)
        # Extract tag data
        t = auto.File(self.full_path)
        self.bitrate =  t.bitrate
        self.duration = t.duration

        return True

class TrackFLAC(Track):
    """Place holder sub-class to handle FLAC files"""
    pass

class Transcoder(object):
    """Transcoder for Track objects"""
    def __init__(self, t):
        if isinstance(t, Track):
            self.track = t
        else:
            print "Transcoder must be passed a Track object"
            sys.exit(1)

    def reencode(self, bitrate, archive_location):
        """Re-encodes the file associated with the Track object"""

        if not os.path.exists(archive_location):
            return False

        if not os.path.exists(self.track.path):
            return False

        os.chdir(self.track.path)

        src_file = self.track.file
        (root, ext) = os.path.splitext(self.track.file)

        if isinstance(self.track, TrackFLAC):
          new_file = "%s.wav" % root
          cmd = 'flac -o "%s" -d "%s"' % (new_file, src_file)
          (exitcode, self.output) = commands.getstatusoutput(cmd)

          if exitcode == 0:
            src_file = new_file
          else:
            return False

        tmp_file = "%s.new" % root
        new_file = "%s.mp3" % root
        cmd = 'lame -S -h -b %s "%s" "%s"' % (bitrate, src_file, tmp_file)
        (exitcode, self.output) = commands.getstatusoutput(cmd)

        if exitcode == 0:
            shutil.move(self.track.file, archive_location)
            shutil.move(tmp_file, new_file)
            if isinstance(self.track, TrackFLAC) and os.path.isfile(src_file):
              os.unlink(src_file)
            return True
        else:
            return False


def usage():
    print 'usage: processmp3 [-l <file processing limit>] <source directory> <archive directory>'
    sys.exit(1)


def main():
    args = sys.argv[1:]
    file_counter = 0
    file_limit = -1

    print "===> Process mp3 - version 1.2"

    if not args:
        usage()

    if args[0] == '-l':
        if not (re.search(r'\d+', args[1])):
            usage()
        file_limit = int(args[1])
        del args[0:2]

    if len(args) != 2:
        usage()

    if os.path.exists(args[0]) and os.path.exists(args[1]):
        source  = os.path.abspath(args[0])
        archive = os.path.abspath(args[1])
    else:
        usage()


    print "==> Scanning source directory for FLACs..."

    for f in glob.glob("%s/*.flac" % source):
        t = TrackFLAC()
        if t.parse(f):
            print "=> Processing %s" % t.track
            print "File Name: %s" % t.file

            sys.stdout.write("Transcoding... ")
            sys.stdout.flush()
            tc = Transcoder(t)

            if tc.reencode("128", archive):
                print "completed."
                file_counter = file_counter + 1
            else:
                print "failed!"

            if file_limit != -1 and file_counter >= file_limit:
                break

    print "==> Scanning source directory for mp3s..."

    for f in glob.glob("%s/*.mp3" % source):
        t = TrackMP3()
        if t.parse(f) and t.bitrate > 128:
            print "=> Processing %s" % t.track
            print "File Name: %s" % t.file
            print "Bitrate: %s" % t.bitrate
            print "Duration: %s" % t.duration

            sys.stdout.write("Transcoding... ")
            sys.stdout.flush()
            tc = Transcoder(t)

            if tc.reencode("128", archive):
                print "completed."
                file_counter = file_counter + 1
            else:
                print "failed!"

            if file_limit != -1 and file_counter >= file_limit:
                break

    print "==> Completed"
    print "Files processed: %d" % file_counter

if __name__ == '__main__':
  main()
