*********
Changelog
*********

See the `Releases page`_ on GitHub for a complete list of commits that are
included in each version.


1
----
2
====
3
####
4
""""

8.2.11 (2024-Jun-12)
--------------------

Core
====

Plugins
#######

Dotnet
""""""

Fixes a regression where the dotnet plugin could not be used for core22 snaps.

8.2.10 (2024-Jun-03)
--------------------

8.2.9 (2024-May-28)
-------------------

8.2.8 (2024-May-17)
-------------------

8.2.7 (2024-May-09)
-------------------

8.2.6 (2024-May-09)
-------------------

8.2.5 (2024-May-07)
-------------------

8.2.4 (2024-May-05)
-------------------

8.2.3 (2024-May-01)
-------------------

8.2.2 (2024-Apr-30)
-------------------

8.2.1 (2024-Apr-25)
-------------------

8.2.0 (2024-Apr-17)
-------------------

8.1.0 (2024-Apr-10)
-------------------

Core
====

Finalized support for core24
############################

Snapcraft builds core24 snaps via `craft-application`_. The integration of
craft-application into Snapcraft is complete, which means the build behavior
for core24 snaps is finalized. See more details on deprecations and changes
in the `core24 migration guide`_.

Snap components
###############

Components are parts of a snap that can be built and uploaded in conjunction
with a snap and later optionally installed beside it. Components are defined
with a top-level ``components`` keyword in a ``snapcraft.yaml``.

Snapcraft allows building and uploading components. Documentation and
ecosystem-wide support (i.e. snapd and the Snap Store) are still in progress,
so components are not ready for production use.

Plugins
#######

Matter SDK
""""""""""

The Matter SDK plugin allows for creating `Matter`_ applications for core22
snaps. See the `Matter on Ubuntu`_ docs for information on Matter.

Maven
"""""

The Maven plugin can be used for core22 snaps.
See :doc:`/reference/plugins/maven` for more information.

QMake
"""""

The QMake plugin can be used for core22 snaps.
See https://snapcraft.io/docs/qmake-plugin for more information.

Colcon
""""""

If a build-type is not provided
(i.e. ``colcon_cmake_args: ["-DCMAKE_BUILD_TYPE=Debug"]``), then the default
build type will be set to ``RELEASE``.

Extensions
##########

KDE Neon 6
""""""""""

The ``kde-neon-6`` extension can be used for ``core22`` snaps that use Qt6 or the
KDE Neon 6 framework.

Remote build
============

The remote-builder supports user-defined Launchpad projects (including
private projects) for core24 snaps. This is configured via
``snapcraft remote-build --project <project-name>``. Support for other bases
will be available in an upcoming release.

8.0.5 (2024-Mar-18)
-------------------

Core
====

* Fixes a bug where Snapcraft could not parse LXD versions with an "LTS" suffix.

8.0.4 (2024-Mar-04)
-------------------

Core
====

Bases
#####

* Fixes a bug where ``devel`` bases may not be fully validated.
* Uses ``buildd`` daily images instead of ``ubuntu`` images for ``core24``
  ``devel`` bases.
* Bumps the LXD compatibility tag to ``v7``.
* Fixes a bug where creating the base image would fail because ``apt``
  was installing packages interactively.

8.0.3 (2024-Feb-09)
-------------------

Core
====

* Adds a warning when a part uses ``override-prime`` cannot use
  ``enable-patchelf``.

Bases
#####

* The ``devel`` base no longer updates ``apt`` source config files.
* ``core24`` now uses the ``core24`` alias instead of the ``devel`` alias
  when retrieving LXD images.
* Bumps the LXD compatibility tag to ``v6``.

Plugins
#######

Ant plugin
""""""""""

The ``ant`` plugin now honors proxy environment variables, ``http_proxy``
and ``https_proxy``.

Remote build
============

* Better error messages and links to documentation when remote builds fail.
* ``--build-for`` and ``--build-on`` are now mutually exclusive options.
* The new remote-builder accepts comma-separated values for ``--build-for``
  and ``-build-on``.

8.0.2 (2024-Jan-23)
-------------------

Core
====

* Fixes a bug where Snapcraft would fail to run on platforms where
``SSL_CERT_DIR`` is not set.
* Fixes a decoding bug when logging malformed output from other processes
  (typically during the ``build`` step).

8.0.1 (2024-Jan-03)
-------------------

Remote build
============
* Snapcraft will now fail if the remote build fails with the new and legacy
  remote builders
* Large repos can be pushed to launchpad with the new remote builder
* Shallowly-cloned repos will fall back to use the legacy remote builder

8.0.0 (2023-Dec-04)
-------------------

Core
====

core18 base removal
###################

This is the largest change and the main reason for the major version bump.
Builds requiring core18 should stick to Snapcraft 7.x. For information on how
to install 7.x and 8.x, see https://snapcraft.io/docs/parallel-installs.

Remote building for this base will still work, but will issue a warning.

Command line
############

The command line has been improved so that messages are streamed in the default
brief mode, with additional tuning of the wording, replacing the message
``Executing`` to ``Pulling``, ``Building``, ``Staging``, and ``Priming``,
making the message much more compact and to the point.


New environment for architecture
################################

New environment is available to refer to the build-on and build-for architectures, for core22:

* ``CRAFT_ARCH_TRIPLET_BUILD_FOR``, supersedes ``CRAFT_ARCH_TRIPLET``
* ``CRAFT_ARCH_TRIPLET_BUILD_ON``
* ``CRAFT_ARCH_BUILD_FOR``, supersedes ``CRAFT_TARGET_ARCH``
* ``CRAFT_ARCH_BUILD_ON``

For core20:

* ``SNAPCRAFT_ARCH_TRIPLET_BUILD_FOR``, supersedes ``SNAPCRAFT_ARCH_TRIPLET``
* ``SNAPCRAFT_ARCH_TRIPLET_BUILD_ON``
* ``SNAPCRAFT_ARCH_BUILD_FOR``, supersedes ``SNAPCRAFT_TARGET_ARCH``
* ``SNAPCRAFT_ARCH_BUILD_ON``

More on this can be read at :doc:`/reference/architectures`.

Linter
######

The linter is now capable of showing what package could be provided through
``stage-packages`` to satisfy a potential missing library.

Chiseling
#########

Chiseled packages can now be referenced through stage-packages, the chiseled
slices can be referred to by their name. The current behavior is that when you
would opt-in for chiseled packages, you can not mix that with regular debian
packages.

This is a great option for creating bases or when using bare as a base.

More about Chisel can be found at https://github.com/canonical/chisel


Plugins and Extensions
######################

Rust plugin
===========

The rust plugin has been significantly improved for core20 and core22 bases.
The requirement to speficy the rust toolchain is no longer there and the plugin
will fetch the toolchain using rustup as previous versions of this plugin once
did.

More information about the new options for rust can be found at
:doc:`/reference/plugins/rust_plugin`.

Kernel plugin
=============

The kernel plugin can now properly generate Ubuntu kernel configs.

Python plugin
=============

The plugin finally supports PEP 518, essentially meaning that projects can be
driven through a pyproject.toml.

ROS content sharing
===================

Support for content sharing for ROS powered by the extensions that make
building a ROS content sharing snap seamless.

To that effect several snaps meant to distribute ROS through content-sharing
were created and are available on the store (hidden, e.g. ros-foxy-ros-base &
ros-foxy-ros-base-dev)

The support is introduced for

* the core20 & core22 bases (ROS Noetic, Foxy, Humble)
* the colcon, catkin, and catkin-tools plugins

To note, this requires the dev snap providing the build-time material to
execute a script listing all ROS packages it contains when it's built.

The general architecture is neatly described at
https://ubuntu.com/robotics/docs/ros-architectures-with-snaps.
More information on each extension behavior can be found at:

* https://snapcraft.io/docs/ros2-humble-content-extension
* https://snapcraft.io/docs/ros2-foxy-content-extension
* https://snapcraft.io/docs/ros-noetic-content-extension


Remote build
============

Note that this is for core22 and earlier bases. Core24 bases and onward have a
different design.

Remote build has an improved behavior. In the past any local source would have
been tarballed, generating a new ``snapcraft.yaml`` before pushing to launchpad
to ensure that all sources could be read. This presented many problems, one of
which was that the remote build process was not building as it would have when
running locally.

All this has been fixed with the new git first workflow in remote-build,
there's now an environment variable, ``SNAPCRAFT_REMOTE_BUILD_STRATEGY`` that can
be set to:

* ``disable-fallback`` to force the new feature
* ``force-fallback`` to force the legacy feature of tarballing the sources

The new feature requires snapcraft projects to be in the top-level of a git
repository. Shallowly cloned repositories are not supported
(``git clone --depth=``) because they cannot be pushed to Launchpad.

See more information at https://snapcraft.io/docs/remote-build.

Store
=====

Store operations no longer require a working keyring, Snapcraft will correctly
fallback to a file based keyring in these scenarios when working on headless
systems or when the system's keyring is not fully configured. The documentation
on https://snapcraft.io/docs/snapcraft-authentication has been updated to
reflect this, with additional edits to streamline for the new features and
hiding away the legacy ones.

For a complete list of commits, check out the `8.0.0`_ GitHub release.

.. _Releases page: https://github.com/canonical/snapcraft/releases
.. _craft-application: https://github.com/canonical/craft-application
.. _core24 migration guide: https://snapcraft.io/docs/migrate-core24
.. _Matter: https://csa-iot.org/all-solutions/matter/
.. _Matter on Ubuntu: https://canonical-matter.readthedocs-hosted.com/en/latest/

.. |release_url| replace:: https://github.com/canonical/snapcraft/releases/tag/

.. _8.0.0: |release_url|8.0.0
