new MudObject class is finished!
	a basic security framework is in place, need to figure out how make it a metaclass and get the permission
	checking to be more "automatic".
	
	the current way of checking security is very basic:
		the "owner" instance and itself (self) has full access to a MudProperty
		groups are supported, but not fully implimented
		
