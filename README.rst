**************
`tpg_invoice`_
**************

Extracts tax invoices from the `TPG`_ Cyberstore (My Account) at the command
line.

This is useful for automatically grabbing tax invoices.

This has only been tested with a fixed broadband service.  It has not been
tested with other products (eg: mobile, dial-up).

*This is software is not written or endorsed by* `TPG`_.

Installing
==========

The easiest way to install ``tpg_invoice`` is::

	$ pip3 install tpg_invoice

Manual installation
-------------------

``tpg_invoice`` requires the following:

* Python 3 (tested on 3.6)
* BeautifulSoup4
* requests

In Debian based distributions, install these packages::

	apt install python3 python3-requests python3-bs4

Then run::

	./setup.py install

Authentication
==============

``tpg_invoice`` supports authentication with a username and password, or a
pre-existing session cookie.  One of the mechanisms must be specified.

Authenticating with a username and password
-------------------------------------------

Usage::

	$ tpg_invoice -s ~/.config/tpg.secrets

``tpg.secrets`` is a text file, with two lines:

#. TPG username.
#. Account password.

An example secrets file is given below, where the username is ``exampleuser``
and their password is ``correcthorsebatterystaple``::

	exampleuser
	correcthorsebatterystaple

Make sure to keep this file only readable by the user which ``tpg_invoice`` runs
as.

Rate limits apply to the login form, even when login was successful.

Authenticating with a session cookie
------------------------------------

Usage::

	$ tpg_invoice -S 5wxbc9p2wjhvgssfl0b7nevgfou

This uses an existing ``TPGSESS`` cookie to make requests to TPG.

Usage
=====

Get invoice list: ``tpg_invoice list``
--------------------------------------

Usage::

	$ tpg_invoice -s tpg.secrets list
	Invoice list:

	I178018865: raised 2018-01-01, $59.99
	I184856374: raised 2018-02-01, $59.99
	[...]

Get specific invoice(s): ``tpg_invoice get I...``
-------------------------------------------------

Returns a specific invoice as HTML::

	$ tpg_invoice -s tpg.secrets get I178018865
	<div class="iaspage-area">Tax Invoice Display<table align="RIGHT"><!--/home/database/cgi-bin/inv_disp.cgi:153--><tr><td align="RIGHT">TPG Internet Pty Ltd ABN 15 068 383 737</td></tr><tr><td align="RIGHT">65 Waterloo Rd, MACQUARIE PARK, NSW, 2113</td></tr></table>
	[...]

Multiple invoice IDs may be specified at the command line.  They will be shown separated by a blank line::

	$ tpg_invoice -s tpg.secrets get I178018865 I184856374
	<div class="iaspage-area">Tax Invoice Display<table align="RIGHT"><!--/home/database/cgi-bin/inv_disp.cgi:153--><tr><td align="RIGHT">TPG Internet Pty Ltd ABN 15 068 383 737</td></tr><tr><td align="RIGHT">65 Waterloo Rd, MACQUARIE PARK, NSW, 2113</td></tr></table>
	[...]

	<div class="iaspage-area">Tax Invoice Display<table align="RIGHT"><!--/home/database/cgi-bin/inv_disp.cgi:153--><tr><td align="RIGHT">TPG Internet Pty Ltd ABN 15 068 383 737</td></tr><tr><td align="RIGHT">65 Waterloo Rd, MACQUARIE PARK, NSW, 2113</td></tr></table>
	[...]

Get the latest invoice: ``tpg_invoice get --latest``
----------------------------------------------------

Returns the latest, non-$0 invoice as HTML::

	$ tpg_invoice -s tpg.secrets get --latest
	<div class="iaspage-area">Tax Invoice Display<table align="RIGHT"><!--/home/database/cgi-bin/inv_disp.cgi:153--><tr><td align="RIGHT">TPG Internet Pty Ltd ABN 15 068 383 737</td></tr><tr><td align="RIGHT">65 Waterloo Rd, MACQUARIE PARK, NSW, 2113</td></tr></table>
	[...]

Email the latest invoice: ``email_invoice.sh``
----------------------------------------------

``email_invoice.sh`` will let you automatically email the latest, non-$0
invoice.  This is useful if you need to automatically send your TPG invoices to
your accountant, bookkeeper, or expense reporting system.

This has been primarily tested with Concur, which converts incoming HTML emails
to PDF automatically, and adds them as an available receipt. For more details on
configuring Concur to receive receipts from additional email addresses, please
see the Concur documentation.

This script is designed to be run as a ``cron(8)`` job, and will need to be
modified to your local needs (such as setting the destination email address,
and the subject line).

The script requires that you have the BSD ``mail(1)`` package configured to be
able to send outgoing email, which generally requires a local MTA.

``fmt(1)`` is required to split long lines in the output, as the SMTP protocol
specifies that lines must be less than 998 characters. The typical invoice
output is more than this, and can cause some MTAs to reject the email outright.

.. _TPG: https://www.tpg.com.au/
.. _tpg_invoice: https://github.com/micolous/tpg_invoice

