#!/bin/sh

# This script creates the mysql data directory during first service start.
# In subsequent starts, it does nothing much.

source "`dirname ${BASH_SOURCE[0]}`/mysql-scripts-common"

# If two args given first is user, second is group
# otherwise the arg is the systemd service file
if [ "$#" -eq 2 ]
then
    myuser="$1"
    mygroup="$2"
else
    # Absorb configuration settings from the specified systemd service file,
    # or the default service if not specified
    SERVICE_NAME="$1"
    if [ x"$SERVICE_NAME" = x ]
    then
        SERVICE_NAME=@DAEMON_NAME@.service
    fi

    myuser=`systemctl show -p User "${SERVICE_NAME}" |
      sed 's/^User=//'`
    if [ x"$myuser" = x ]
    then
        myuser=mysql
    fi

    mygroup=`systemctl show -p Group "${SERVICE_NAME}" |
      sed 's/^Group=//'`
    if [ x"$mygroup" = x ]
    then
        mygroup=mysql
    fi
fi

# Set up the errlogfile with appropriate permissions
if [ ! -e "$errlogfile" -a ! -L "$errlogfile" ]; then
    touch "$errlogfile"
    chown "$myuser:$mygroup" "$errlogfile"
    chmod 0640 "$errlogfile"
fi
su - $myuser -s /bin/bash -c "touch '$errlogfile'"
ret=$?
# Provide some advice if the log file cannot be touched
if [ $ret -ne 0 ] ; then
    errlogdir=$(dirname $errlogfile)
    if ! [ -d "$errlogdir" ] ; then
        echo "The directory $errlogdir does not exist."
    elif [ -f "$errlogfile" ] ; then
        echo "The log file $errlogfile cannot be touched, please, fix its permissions."
    else
        echo "The log file $errlogfile could not be created."
    fi
    echo "The daemon will be run under $myuser:$mygroup"
    exit 1
fi
[ -x /sbin/restorecon ] && /sbin/restorecon "$errlogfile"

# Make sure $datadir is there with correct permissions
if [ ! -e "$datadir" -a ! -L "$datadir" ]; then
    mkdir -p "$datadir" || exit 1
    chown "$myuser:$mygroup" "$datadir"
    chmod 0755 "$datadir"
fi
[ -x /sbin/restorecon ] && /sbin/restorecon "$datadir"

if [ ! -d "$datadir/mysql" ] ; then
    # Now create the database
    echo "Initializing @NICE_PROJECT_NAME@ database"
    su - $myuser -s /bin/bash -c "@bindir@/mysql_install_db --rpm --datadir='$datadir' --user='$myuser'"
    ret=$?
    if [ $ret -ne 0 ] ; then
        echo "Initialization of @NICE_PROJECT_NAME@ database failed." >&2
        echo "Perhaps @sysconfdir@/my.cnf is misconfigured." >&2
        echo "Note, that you may need to clean up any partially-created database files in $datadir" >&2
        exit $ret
    fi
    # upgrade does not need to be run on a fresh datadir
    su - $myuser -s /bin/bash -c "echo '@VERSION@' > '$datadir/mysql_upgrade_info'"
fi

exit 0
