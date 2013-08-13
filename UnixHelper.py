import os, pwd, grp

def drop_privileges(uid_name, gid_name):
    """ Drop privileges to given user name and group.
        Returns True on success and False on failure. """
    try:
        running_uid = pwd.getpwnam(uid_name).pw_uid
        running_gid = grp.getgrnam(gid_name).gr_gid
        
        cur_uid = os.getuid()
        if cur_uid != 0:
            #We're not root. But if we are already running as correct
            #user and group, we won't fail.
            return cur_uid == running_uid and os.getgid() == running_gid
        
        os.setgroups([])
        
        os.setgid(running_gid)
        os.setuid(running_uid)
        
        old_umask = os.umask(0o077)
        
        return True    
    except:
        return False
