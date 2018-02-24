#!/usr/bin/env python3
# -*- mode: python; indent-tabs-mode: nil; tab-width: 3; coding: utf-8 -*-
'''
tpg_invoice.py
Extracts invoices from the TPG (www.tpg.com.au) website.

Copyright 2018 Michael Farrell <micolous+git@gmail.com>

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
'''

from argparse import ArgumentParser, FileType
from bs4 import BeautifulSoup
from datetime import datetime
from decimal import Decimal
import random
import requests
from urllib.parse import parse_qs

TPG_LOGIN_FORM = b'https://www.tpg.com.au/home/myaccount'
TPG_LOGIN = b'https://cyberstore.tpg.com.au/your_account/'
TPG_CYBERSTORE = b'https://cyberstore.tpg.com.au/your_account/index.php'
USER_AGENT = b'Mozilla/5.0 (X11; Linux x86_64; rv:20.1) Gecko/20100101 Firefox/20.1'

class TPGException(Exception): pass

def parse_isodate(s):
   return datetime.strptime(s, '%Y-%m-%d').date()


class TPGInvoiceListItem:
   def __init__(self, row, header):
      c = row.find_all('td')
      
      self.invoice_number = c[header['number']].text.strip()
      self.user_number = c[header['user num']].text.strip()
      self.username = c[header['username']].text.strip()
      self.raised = parse_isodate(c[header['raised']].text.strip())

      self.amount = c[header['amount']].text.strip()
      
      if self.amount.startswith('$'):
         self.amount = self.amount[1:]

      self.amount = Decimal(self.amount)
      
      qs = parse_qs(c[header['number']].a.get('href'))
      self.refer = qs['refer'][0]


   def __repr__(self):
      return '<TPGInvoiceListItem refer=%r, invoice_number=%r, user_number=%r, username=%r, raised=%r, amount=%r>' % (
         self.refer,
         self.invoice_number,
         self.user_number,
         self.username,
         self.raised,
         self.amount,
      )


class TPGAccountPortal:
   def __init__(self):
      self._session = requests.Session()
      self._session.headers.update({b'User-agent': USER_AGENT})

   def login(self, username, password):
      '''
      Logs in to the TPG Cyberstore, and gets a session cookie. This must be
      called before any other operation.
      
      Raises TPGException on errors.
      '''

      # Get a session cookie
      r = self._session.post(TPG_LOGIN, data=dict(
         x=str(random.randint(0,77)),
         y=str(random.randint(0,35)),
         password1=b'Password',
         check_username=username,
         password=password,
      ), headers={
         b'Referer': TPG_LOGIN_FORM,
      })
      
      if r.status_code != 200:
         raise TPGException('Got non-200 response code (%d)' % r.status_code)

      # Even "wrong password" gives a 200 response.
      # Check for rate limiting
      if 'too many login attempts' in r.text:
         raise TPGException('Too many login attempts for username / IP, try again later.')
      
      # Look for a link to the "Your Invoices" page
      if 'function=accountdocs' not in r.text:
         #print(r.text)
         raise TPGException('Could not find invoices link. Login details may be incorrect.')


   def add_session(self, session):
      '''
      Instead of logging in, add a `TPGSESS` cookie to log in with. This is
      useful during development if rate limited.

      '''
      self._session.cookies.set('TPGSESS', session, domain='cyberstore.tpg.com.au')


   def get_invoice_list(self):
      '''
      Gets a list of invoices associated with the account.
      '''
      r = self._session.get(TPG_CYBERSTORE,
         params={'function': 'accountdocs'},
         headers={
            b'Referer': TPG_LOGIN,
         })
     
      if r.status_code != 200:
         raise TPGException('Got non-200 response code (%d)' % r.status_code)

      # Check if this looks like the Invoice List page
      if 'Account Display' not in r.text:
         raise TPGException('This does not look like the invoice list page.')

      return self.parse_invoice_list(r.text)

   def parse_invoice_list(self, page):
      # Parse list of available invoices.
      #print(page)
      soup = self._get_main_soup(page)
      header = None
      for row in soup.table.find_all('tr'):
         #print(row)

         if header is None:
            # Map out the column headers
            h = row.find(lambda x: x.name == 'td' and 'number' in x.string.lower())
            if h is not None:
               header = {}
               for i, c in enumerate(row.find_all('td')):
                  s = c.string
                  if s is None:
                     continue
                  header[s.strip().lower()] = i
               #print(header)

         if row.a is None:
            # This is not an invoice row
            continue
         
         yield TPGInvoiceListItem(row, header)

   def get_invoice_detail(self, refer):
      '''
      Gets a single invoice, given the `refer` code from a TPGInvoiceListItem.

      '''
      r = self._session.get(TPG_CYBERSTORE,
         params={
            'function': 'accountdocs',
            'refer': refer,
         },
         headers={
            b'Referer': TPG_CYBERSTORE,
         })
     
      if r.status_code != 200:
         raise TPGException('Got non-200 response code (%d)' % r.status_code)

      # Check if this looks like the Invoice List page
      if 'Invoice Display' not in r.text:
         raise TPGException('This does not look like the invoice detail page.')

      return self.parse_invoice_detail(r.text)

   def parse_invoice_detail(self, page):
      # Parse invoice detail
      #print(page)
      soup = self._get_main_soup(page)
      if soup.link is not None:
         # Remove the style-sheet from the page (it is broken anyway)
         soup.link.decompose()

      # Emit the page
      return str(soup)

   def _get_main_soup(self, page):
      soup = BeautifulSoup(page, 'html.parser')
      d = soup.find_all('div', attrs={'class': 'iaspage-area'})
      return d[0]
      

def read_username_password(fh):
   username = fh.readline().strip()
   password = fh.readline().strip()
   fh.close()
   return (username, password)


def main():
   parser = ArgumentParser(description='Extracts invoices from the TPG (www.tpg.com.au) website.')
   
   group_auth = parser.add_mutually_exclusive_group(required=True)

   group_auth.add_argument('-s', '--secrets', type=FileType('r'),
      help='Authenticates with a new session, using a file containing your TPG username and password, separated by newline.')

   group_auth.add_argument('-S', '--session',
      help='Authenticate using an existing TPGSESS cookie value. This mode is useful when testing, as TPG rate limit authentication attempts.')

   subparsers = parser.add_subparsers(help='Action to perform')

   parser_list = subparsers.add_parser('list', help='Gets a list of invoices.')
   parser_list.set_defaults(action='list')
   
   parser_detail = subparsers.add_parser('get', help='Gets a specific invoice.')
   parser_detail.set_defaults(action='get')

   parser_detail.add_argument('invoice_number', nargs='*',
      help='Gets specific invoice number(s). These typically start with "I".')

   parser_detail.add_argument('--latest', action='store_true',
      help='Gets the newest invoice, excluding those which are $0.')

   options = parser.parse_args()
   
   if options.action == 'get':
      if not options.latest and not options.invoice_number:
         print('Must specify either --latest or at least one invoice number.')
         return

   portal = TPGAccountPortal()
   
   # Authenticate
   if options.secrets:
      username, password = read_username_password(options.secrets)
      portal.login(username, password)
   elif options.session:
      portal.add_session(options.session)
   else:
      print('unknown authentication mechanism')
      return

   invoices_requested = set()
   latest_invoice = None

   # Find all the invoices
   if options.action == 'list':
      print('Invoice list:')
      print()

   for invoice in portal.get_invoice_list():
      if options.action == 'list':
         print('%s: raised %s, $%s' % (
            invoice.invoice_number,
            invoice.raised.isoformat(),
            invoice.amount,
         ))
   
      if options.action == 'get':
         # Find the latest invoice
         if options.latest:
            if latest_invoice is None:
               latest_invoice = invoice
               continue

            if latest_invoice.raised < invoice.raised and invoice.amount != 0:
               latest_invoice = invoice
               continue

         # Find specific invoice(s)
         if options.invoice_number:
            for i in options.invoice_number:
               if invoice.invoice_number == i:
                  invoices_requested.add(invoice.refer)
                  options.invoice_number.remove(i)

   if options.action != 'get':
      return

   # Check if there are left overs
   if options.invoice_number:
      print('Warning: Could not find invoices: %r' % (options.invoice_number,))

   if latest_invoice:
      invoices_requested.add(latest_invoice.refer)

   for invoice in invoices_requested:
      try:
         i = portal.get_invoice_detail(invoice)
         print(i)
         print('')
      except TPGException:
         print('Error fetching invoice %r' % (invoice,))
         print(ex)
         continue


if __name__ == '__main__':
   main()

