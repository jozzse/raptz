
ARG_LNAME=0
ARG_SNAME=1
ARG_VAL=2
ARG_DEF=3
ARG_HLP=4

def space_out(string, size, start = 0):
	endspaces = size - (start + len(string))
	if endspaces < 0:
		start = start + endspaces
		if start < 0:
			return string[:size]
		return "".join([" "*start, string])
	return "".join([" "*start, string, " "*endspaces])

class RargsArgs(object):
	def __init__(self, name, func, hlp):
		self.__hlp = hlp
		self.__func = func
		self.__name = name
		self.__largs = {}
		self.__sargs = {}
		self.__dashdash = False

	def Name(self):
		return self.__name

	def DashDashArgs(self, use):
		self.__dashdash = use

	def Func(self):
		return self.__func()
	
	def Help(self):
		return self.__hlp
	
	def AddArg(self, lname, sname=None, default=None, hlp=""):
		arg = [lname, sname, default, default, hlp]
		if default == None:
			arg[ARG_VAL] = False

		self.__largs[lname] = arg
		if sname:
			self.__sargs[sname] = lname

	def Get(self, name):
		if not name:
			return None
		if name in self.__largs:
			return self.__largs[name][ARG_VAL]
		return None

	def  __getattr__(self, name):
		val = self.Get(name)
		if val == None:
			return object.__getattribute__(self, name)
		return val

	def GetHelp(self):
		txt = []
		for arg in self.__largs.values():
			line = ""
			sarg = ""
			default = ""
			if arg[ARG_SNAME]:
				sarg = "-" + arg[ARG_SNAME] + ", "
			if arg[ARG_DEF] == None:
				line = space_out(sarg + "--" + arg[ARG_LNAME], 24, 4)
			else:
				line = space_out(sarg + "--" + arg[ARG_LNAME] + " <val> ", 24, 4) 
				default = '  (default="' + arg[ARG_DEF] + '")'
			txt.append(line + arg[ARG_HLP] + default)
			if self.__dashdash:
				txt.append(space_out("--", 24, 4) + "subcommand commands")
		return "\n".join(txt)

	def Parse(self, inargs):
		retargs = []
		while inargs and inargs != [] and inargs != [None]:
			inarg = inargs[0]
			if inarg == "--":
					return retargs + inargs
			del inargs[0]
			arg = None
			if inarg.startswith("-") and len(inarg) == 2:
				if inarg[1] in self.__sargs:
					inarg = "--" + self.__sargs[inarg[1]]
			if inarg.startswith("--"):
				if len(inarg) > 2 and inarg[2:] in self.__largs:
					arg = self.__largs[inarg[2:]]
			if arg:
				if arg[ARG_DEF] == None:
					arg[ARG_VAL] = True
				else:
					if len(inargs):
						arg[ARG_VAL] = inargs[0]
						del inargs[0]
					else:
						print 'No value for argument "' + inarg + '"'
						exit(1)
			else:
				retargs.append(inarg)
		return retargs


CMD_NAME=0
CMD_FUNC=1
CMD_HLP=2

class Rargs(RargsArgs):
	def __init__(self, hlp):
		RargsArgs.__init__(self, "", self.PrintHelp, hlp)
		self.__cmds = {}
		self.__command = None
		self.AddCmd("help", self.PrintHelp, "Print this help text")
		self.AddArg("help", "h", None, "Print this command help text")

	def Func(self):
		if self.help:
			return self.PrintHelp()
		if self.__command:
			return self.__command.Func()
		return None

	def PrintHelp(self):
		if self.__command == self.__cmds["help"]:
			self.__command = None
		print self.GetHelp()

	def Get(self, name):
		val = RargsArgs.Get(self, name)
		if val == None and self.__command:
			return self.__command.Get(name)
		return val

	def AddCmd(self, name, func=None, hlp=""):
		ra = RargsArgs(name, func, hlp)
		self.__cmds[name] = ra
		return ra

	def GetHelp(self):
		if not self.__command:
			txt = ["", self.Help(), "", "Commands:"]
			for cmd in self.__cmds:
				txt.append(space_out(cmd, 24, 4) + "    " + self.__cmds[cmd].Help())
			
			return "\n".join(txt)
		else:
			cmd = "Command: " + self.__command.Name() 
			txt = [self.Help(), "", cmd, "    " + self.__command.Help(),"", "Arguments:"]
			txt.append(RargsArgs.GetHelp(self))
			txt.append(self.__command.GetHelp())
			return "\n".join(txt)

	def Parse(self, args):
		if not args or not len(args):
			print "No subcommand"
			print ""
			print self.GetHelp()
			exit(1)
		if args[0] == "--help" or args[0] == "-h":
			print self.GetHelp()
			exit(1)
		if not args[0] in self.__cmds:
			print "Subcommand \"" + args[0] + "\" Not found"
			print ""
			print self.GetHelp()
			exit(1)
		self.__command = self.__cmds[args[0]]
		del args[0]
		args = RargsArgs.Parse(self, args)
		args = self.__command.Parse(args)
		if len(args):
			if args[0] != "--":
				print "Unkonwn commands " + " ".join(args)
				print ""
				print self.GetHelp()
				exit(1)
			return args[1:]
		return args



