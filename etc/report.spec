%define name report

Summary: report service
Name: %{name}
Version: 1.0
Release: 201603031100
Source0: %{name}-%{version}-%{release}.tar.gz


License: Apache License, Version 2.0
Group: Applications/System
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-buildroot
Prefix: %{_prefix}
BuildArch: noarch
Vendor: OpenStack <openstack-dev@lists.openstack.org>
Url: https://launchpad.net/report


# we dropped the patch to remove PBR for Delorean
Requires:         python-pbr
# as convenience
Requires(post):   systemd
Requires(preun):  systemd
Requires(postun): systemd

Requires:         python-eventlet
Requires:         python-tzlocal
Requires:         APScheduler
Requires:         python-cairosvg
Requires:         python-jinja2
Requires:         libyaml >= 0.1.4
Requires:         MySQL-python >= 1.2.3
Requires:         python2-oslo-config >= 2.4.0
Requires:         python2-oslo-context >= 0.6.0
Requires:         python2-oslo-i18n >= 2.6.0
Requires:         python2-oslo-serialization >= 1.9.0
Requires:         python2-oslo-utils >= 2.5.0
Requires:         python2-pecan >= 1.0.2
Requires:         python2-PyMySQL >= 0.6.7
Requires:         python2-wsme >= 0.7.0
Requires:         python-cairosvg >= 1.0.7
Requires:         python-cssselect >= 0.9.1
Requires:         python-jinja2 >= 2.7.2
Requires:         python-keystoneclient >= 1.7.2
Requires:         python-keystonemiddleware >= 2.3.1
Requires:         python-lxml >= 3.2.1
Requires:         python-memcached >= 1.48
Requires:         python-novaclient >= 2.30.1
Requires:         python-oslo-db >= 2.6.0
Requires:         python-oslo-log >= 1.10.0
Requires:         python-oslo-messaging >= 2.5.0
Requires:         python-oslo-middleware >= 2.8.0
Requires:         python-oslo-service >= 0.9.0
Requires:         python-paste >= 1.7.5.1
Requires:         python-paste-deploy >= 1.5.0
Requires:         python-pbr >= 1.8.1
Requires:         python-pillow >= 2.0.0
Requires:         python-pygal >= 2.0.10
Requires:         python-reportlab >= 2.5
Requires:         python-routes >= 1.13
Requires:         python-sqlalchemy >= 1.0.4
Requires:         python-tinycss >= 0.3
Requires:         PyYAML >= 3.10
Requires:         influxdb-python



%description
Report
======

%prep
%setup -n %{name}-%{version}-%{release}

%build
python setup.py build

%install
python setup.py install --single-version-externally-managed -O1 --root=$RPM_BUILD_ROOT --record=INSTALLED_FILES

# Install config files
install -d -m 755 %{buildroot}%{_sysconfdir}/report
install -p -D -m 640 etc/api-paste.ini        %{buildroot}%{_sysconfdir}/report/api-paste.ini
install -p -D -m 640 etc/report.conf.example  %{buildroot}%{_sysconfdir}/report/report.conf.example
install -p -D -m 640 etc/report.conf.example  %{buildroot}%{_sysconfdir}/report/report.conf
install -p -D -m 640 etc/mail_template.xml    %{buildroot}%{_sysconfdir}/report/mail_template.xml

# Install initscripts for services
install -p -D -m 644 etc/report-api.service   %{buildroot}%{_unitdir}/report-api.service
install -p -D -m 644 etc/report-agent.service %{buildroot}%{_unitdir}/report-agent.service

# Install pid directory
install -p -d -m 755 %{buildroot}%{_localstatedir}/run/report

# install log directory
install -p -d -m 755 %{buildroot}%{_localstatedir}/log/report

# Install data directory
install -p -d -m 755 %{_datadir}/report/rptfiles

%pre
USERNAME=report
GROUPNAME=$USERNAME
HOMEDIR=/home/$USERNAME
getent group $GROUPNAME >/dev/null || groupadd -r $GROUPNAME
getent passwd $USERNAME >/dev/null || useradd -r -g $GROUPNAME -G $GROUPNAME -d $HOMEDIR -s /sbin/nologin -c "OpenStack Report Daemons" $USERNAME
exit 0

%clean
rm -rf "$RPM_BUILD_ROOT"
rm -rf "$RPM_BUILD_DIR/%{name}-%{version}-%{release}"

%post
mkdir -p %{python_sitelib}/report/locale/zh_CN/LC_MESSAGES
msgfmt %{python_sitelib}/report/locale/lang.po -o %{python_sitelib}/report/locale/zh_CN/LC_MESSAGES/lang.mo
%systemd_post report-api.service
%systemd_post report-agent.service

%preun
%systemd_preun report-api.service
%systemd_preun report-engine.service

%postun
%systemd_postun_with_restart report-api.service
%systemd_postun_with_restart report-engine.service

%files -f INSTALLED_FILES
%defattr(-,root,root)
%dir %attr(0755,report,root) %{_localstatedir}/log/report
%dir %attr(0755,report,root) %{_localstatedir}/run/report
%dir %attr(0755,report,root) %{_sysconfdir}/report

%config(noreplace) %attr(-, root, report) %{_sysconfdir}/report/report.conf.example
%config(noreplace) %attr(-, root, report) %{_sysconfdir}/report/report.conf
%config(noreplace) %attr(-, root, report) %{_sysconfdir}/report/api-paste.ini
%config(noreplace) %attr(-, root, report) %{_sysconfdir}/report/mail_template.xml

%{_bindir}/report-api
%{_bindir}/report-agent
%{_unitdir}/report-api.service
%{_unitdir}/report-agent.service

%{python_sitelib}/report
