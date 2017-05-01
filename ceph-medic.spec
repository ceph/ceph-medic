#
# spec file for package ceph-doctor
#

%if ! (0%{?fedora} > 12 || 0%{?rhel} > 5)
%{!?python_sitelib: %global python_sitelib %(%{__python} -c "from distutils.sysconfig import get_python_lib; print(get_python_lib())")}
%{!?python_sitearch: %global python_sitearch %(%{__python} -c "from distutils.sysconfig import get_python_lib; print(get_python_lib(1))")}
%endif

#################################################################################
# common
#################################################################################
Name:           ceph-doctor
Version:        0.0.1
Release:        0
Summary:        Find common issues on Ceph clusters
License:        MIT
Group:          System/Filesystems
URL:            http://ceph.com/
Source0:        %{name}-%{version}.tar.bz2
BuildRoot:      %{_tmppath}/%{name}-%{version}-build
BuildRequires:  python-devel
BuildRequires:  python-setuptools
BuildRequires:  python-virtualenv
BuildRequires:  python-pytest
BuildRequires:  python-tox
%if 0%{?suse_version}
BuildRequires:  python-pytest
%else
BuildRequires:  pytest
%endif
BuildRequires:  git
Requires:       python-remoto
Requires:       python-tambo
Requires:       python-execnet
%if 0%{?suse_version} && 0%{?suse_version} <= 1110
%{!?python_sitelib: %global python_sitelib %(python -c "from distutils.sysconfig import get_python_lib; print get_python_lib()")}
%else
BuildArch:      noarch
%endif

#################################################################################
# specific
#################################################################################
%if 0%{defined suse_version}
%py_requires
%endif

%description
An admin tool to determine common issues on Ceph storage clusters.

%prep
%setup -q

%build

%install
python setup.py install --prefix=%{_prefix} --root=%{buildroot}
install -m 0755 -D scripts/ceph-doctor $RPM_BUILD_ROOT/usr/bin

%clean
[ "$RPM_BUILD_ROOT" != "/" ] && rm -rf "$RPM_BUILD_ROOT"

%files
%defattr(-,root,root)
%doc LICENSE README.rst
%{_bindir}/ceph-doctor
%{python_sitelib}/*

%changelog
