%define _builddir .
%define _sourcedir .
%define _specdir .
%define _rpmdir .

Name: pgcheck
Version: 1.1
Release: 7%{?dist}

Summary: Meta package for pgcheck
License: Yandex License
Packager: Borodin Vladimir <root@simply.name>
Group: System Environment/Meta
Distribution: Red Hat Enterprise Linux

Requires: python-psycopg2 >= 2.5
Requires: python-daemon >= 1.6
Requires: python-lockfile >= 0.9
Requires: python-requests >= 1.1
Requires: python-setuptools

BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-root
BuildArch: noarch

%description
https://github.com/yandex/pgcheck

%install
%{__rm} -rf %{buildroot}
python setup.py install --root=$RPM_BUILD_ROOT --record=INSTALLED_FILES -O1

%clean
rm -rf $RPM_BUILD_ROOT

%files -f INSTALLED_FILES

%changelog
* Fri Oct 03 2014 Sergey Lavrinenko <s@lavr.me>
- Initial rpm
