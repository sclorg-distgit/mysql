%{!?scl_name_base: %global scl_name_base mysql}
%{!?scl_name_version: %global scl_name_version 55}
%{!?scl:%global scl %{scl_name_base}%{scl_name_version}}
%scl_package %scl

# do not produce empty debuginfo package
%global debug_package %{nil}

Summary: Package that installs %scl
Name: %scl_name
Version: 1.1
Release: 23.sc1%{?dist}
License: GPLv2+
Group: Applications/File
Source0: README
Source1: LICENSE
Requires: scl-utils
Requires: %{scl_prefix}mysql-server
BuildRequires: scl-utils-build help2man
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)

%description
This is the main package for %scl Software Collection, which installs
necessary packages to use MySQL 5.5 server. Software Collections allow
to install more versions of the same package by using alternative
directory structure.
Install this package if you want to use MySQL 5.5 server on your system. 

%package runtime
Summary: Package that handles %scl Software Collection.
Group: Applications/File
Requires: scl-utils
Requires(post): policycoreutils-python libselinux-utils

%description runtime
Package shipping essential scripts to work with %scl Software Collection.

%package build
Summary: Package shipping basic build configuration
Group: Applications/File
Requires: scl-utils-build

%description build
Package shipping essential configuration macros to build %scl Software
Collection or packages depending on %scl Software Collection.

%package scldevel
Summary: Package shipping development files for %scl

%description scldevel
Package shipping development files, especially usefull for development of
packages depending on %scl Software Collection.

%prep
%setup -c -T

# This section generates README file from a template and creates man page
# from that file, expanding RPM macros in the template file.
cat >README <<'EOF'
%{expand:%(cat %{SOURCE0})}
EOF

# copy the license file so %%files section sees it
cp %{SOURCE1} .

%build
# generate a helper script that will be used by help2man
cat >h2m_helper <<'EOF'
#!/bin/bash
[ "$1" == "--version" ] && echo "%{scl_name} %{version} Software Collection" || cat README
EOF
chmod a+x h2m_helper

# generate the man page
help2man -N --section 7 ./h2m_helper -o %{scl_name}.7

%install
rm -rf %{buildroot}

%scl_install

# create and own dirs not covered by %%scl_install and %%scl_files
%if 0%{?rhel} <= 6
mkdir -p %{buildroot}%{_datadir}/aclocal
%else
mkdir -p %{buildroot}%{_mandir}/man{1,7,8}
%endif

# During the build of this package, we don't know which architecture it is 
# going to be used on, so if we build on 64-bit system and use it on 32-bit, 
# the %{_libdir} would stay expanded to '.../lib64'. This way we determine 
# architecture everytime the 'scl enable ...' is run and set the 
# LD_LIBRARY_PATH accordingly
cat >> %{buildroot}%{_scl_scripts}/enable << EOF
export PATH=%{_bindir}\${PATH:+:\${PATH}}
export LIBRARY_PATH=%{_libdir}\${LIBRARY_PATH:+:\${LIBRARY_PATH}}
export LD_LIBRARY_PATH=%{_libdir}\${LD_LIBRARY_PATH:+:\${LD_LIBRARY_PATH}}
export MANPATH=%{_mandir}:\${MANPATH}
export CPATH=%{_includedir}\${CPATH:+:\${CPATH}}
EOF

# generate rpm macros file for depended collections
cat >> %{buildroot}%{_root_sysconfdir}/rpm/macros.%{scl_name_base}-scldevel << EOF
%%scl_%{scl_name_base} %{scl}
%%scl_prefix_%{scl_name_base} %{scl_prefix}
EOF

# generate a configuration file for daemon
cat >> %{buildroot}%{_scl_scripts}/service-environment << EOF
# Services are started in a fresh environment without any influence of user's
# environment (like environment variable values). As a consequence,
# information of all enabled collections will be lost during service start up.
# If user needs to run a service under any software collection enabled, this
# collection has to be written into MYSQL55_SCLS_ENABLED variable in
# /opt/rh/sclname/service-environment.
MYSQL55_SCLS_ENABLED="%{scl}"
EOF

# install generated man page
mkdir -p %{buildroot}%{_mandir}/man7/
install -m 644 %{scl_name}.7 %{buildroot}%{_mandir}/man7/%{scl_name}.7

%post runtime
# Simple copy of context from system root to DSC root.
# In case new version needs some additional rules or context definition,
# it needs to be solved.
semanage fcontext -a -e / %{_scl_root} >/dev/null 2>&1 || :
semanage fcontext -a -e /etc/rc.d/init.d/mysqld /etc/rc.d/init.d/%{scl_prefix}mysqld >/dev/null 2>&1 || :
restorecon -R %{_scl_root} >/dev/null 2>&1 || :
restorecon /etc/rc.d/init.d/%{scl_prefix}mysqld >/dev/null 2>&1 || :
selinuxenabled && load_policy || :

%files

%files runtime
%doc README LICENSE
%scl_files
%if 0%{?rhel} <= 6
%{_datadir}/aclocal
%else
%{_mandir}/man*
%endif
%config(noreplace) %{_scl_scripts}/service-environment
%{_mandir}/man7/%{scl_name}.*

%files build
%doc LICENSE
%{_root_sysconfdir}/rpm/macros.%{scl}-config

%files scldevel
%{_root_sysconfdir}/rpm/macros.%{scl_name_base}-scldevel

%changelog
* Fri Mar 28 2014 Honza Horak <hhorak@redhat.com> - 1.1-23
- Include LICENSE also in -build package
  Related: #1072480

* Thu Mar 27 2014 Honza Horak <hhorak@redhat.com> - 1.1-22
- Own all dirs properly
  Resolves: #1079919

* Wed Mar 26 2014 Jan Stanek <jstanek@redhat.com> - 1.1-21
- Fix wrong macro in README
  Related: #1072480

* Wed Mar 26 2014 Jan Stanek <jstanek@redhat.com> - 1.1-20
- Fix unexpanded macro in README
  Resolves: #1072480

* Wed Feb 12 2014 Honza Horak <hhorak@redhat.com> - 1.1-19
- Fix some grammar mistakes in README
  Related: #1061450

* Tue Feb 11 2014 Honza Horak <hhorak@redhat.com> - 1.1-18
- Add LICENSE, README and mysql55.7 man page
  Resolves: #1061450
- Add -scldevel subpackage
  Resolves: #1063355
- Add scl-utils-build requirement to -build package
  Resolves: #1058610
- Use policycoreutils-python in meta package
  Resolves: #1053457

* Fri Nov 22 2013 Honza Horak <hhorak@redhat.com> 1-18
- Remove unnecessary init.d SELinux definition
- Rename environment variable

* Fri Nov 22 2013 Honza Horak <hhorak@redhat.com> 1-16
- Reload SELinux policy after setting it

* Thu Oct 10 2013 Honza Horak <hhorak@redhat.com> 1-15
- Release bump for RHSCL-1.1

* Mon Jun 17 2013 Honza Horak <hhorak@redhat.com> 1-14
- Add CPATH definition into enable script
  Resolves: #967951

* Wed May 22 2013 Honza Horak <hhorak@redhat.com> 1-13
- Run semanage on whole root, BZ#956981 is fixed now
- Require semanage utility to be installed for -runtime package
- Fix MANPATH definition, colon in the end is correct (it means default)
  Resolves: BZ#966383

* Fri May  3 2013 Honza Horak <hhorak@redhat.com> 1-11
- Remove RHEL-5 stuff
- Run semanage for all directories separately, since it has
  problems with definition for whole root

* Thu May  2 2013 Honza Horak <hhorak@redhat.com> 1-9
- Handle context of the init script
- Change context on whole root directory (libselinux is fixed now #953947)
- Add better descriptions for packages
- Create SELinux context rules also for RHEL-5

* Fri Apr 26 2013 Honza Horak <hhorak@redhat.com> 1-8
- fix escaping in PATH variable definition
- change context on all directories separately

* Mon Apr  8 2013 Honza Horak <hhorak@redhat.com> 1-7
- Don't require policycoreutils-python in RHEL-5 or older
- Require mysql-server from the collection as main package
- Build separately on all arches
- Fix Environment variables definition

* Wed Feb 20 2013 Honza Horak <hhorak@redhat.com> 1-6
- Use %%setup macro to create safer build environment

* Thu Nov 08 2012 Honza Horak <hhorak@redhat.com> 1-5
- Mark service-environment as a config file

* Thu Oct 25 2012 Honza Horak <hhorak@redhat.com> 1-4
- create service-environment file to hold information about all collections,
  that should be enabled when service is starting
- fixed environment variable name
- rename spec file-name to correspond with package name

* Wed Oct 17 2012 Honza Horak <hhorak@redhat.com> 1-3
- copy SELinux context from core mysql files

* Thu Oct 04 2012 Honza Horak <hhorak@redhat.com> 1-2
- rename collection to mysql55

* Tue Mar 20 2012 Honza Horak <hhorak@redhat.com> 1-1
- initial packaging

