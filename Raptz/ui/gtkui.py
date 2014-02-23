
from gi.repository import Gtk, Notify, GLib
from baseui import BaseUI

def mklbl(text):
	lbl = Gtk.Label(text)
	lbl.set_alignment(0.0, 0.0)
	lbl.set_ellipsize(2)
	return lbl
class GtkUI(BaseUI):
		
	def __init__(self, logfile, win):
		BaseUI.__init__(self, logfile)	
		Notify.init("Raptz")
		
		self.box = Gtk.VBox(False, 0)
		win.add(self.box)
		
		self.chk = Gtk.CheckButton()
		self.chk.set_label("Close window when done")
		self.chk.set_active(True)
		self.box.pack_start(self.chk, False, True, 3)

		self.frmlbl = mklbl("")
		
		frm = Gtk.Frame()
		frm.set_label_widget(self.frmlbl)
		self.box.pack_end(frm, True, True, 0)

		self.sc = Gtk.ScrolledWindow()
		a = self.sc.get_vadjustment()
		a.connect("changed", self._scroll)

		self.out = mklbl("")
		self.sc.add(self.out)
		frm.add(self.sc)
		self.running=[]
		win.show_all()

	def _scroll(self, a):
		a.set_value(a.get_upper())
	def set_lines(self, lines):
		BaseUI.set_lines(self, lines)

	def _start(self, text, lines):
		self.running.append(text)
		self.frmlbl.set_label(":".join(self.running))

	def start(self, text, lines=None):
		BaseUI.start(self, text, lines)
		GLib.idle_add(self._start, text, lines)

	def _stop(self):
		l = mklbl(self.frmlbl.get_label() + " Done")
		self.box.pack_start(l, False, True, 0)
		self.box.show_all()
		del self.running[-1]
		self.frmlbl.set_label(":".join(self.running))

	def stop(self):
		BaseUI.stop(self)
		GLib.idle_add(self._stop)

	def _line(self, text):
		self.out.set_text(self.out.get_text() + "\n" + text)		
	
	def line(self, text):
		BaseUI.line(self, text)
		GLib.idle_add(self._line, text)

	def message(self, text):
		BaseUI.message(self, text)
		GLib.idle_add(self._line, text)
		Notify.Notification.new ("raptz", text, "dialog-information").show()

