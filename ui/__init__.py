
def init_auto():
	try:
		from gtkui import UI
	except:
		try:
			from cursesui import UI
		except:
			try:
				from textui import UI
			except:
				from rawui import UI
	return UI

def get(uidef):
	if uidef=="auto":
		return init_auto()
	if uidef=="raw":
		from rawui import UI
		return UI
	if uidef=="text":
		from textui import UI
		return UI

	raise
