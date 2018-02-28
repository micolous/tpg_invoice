#!/bin/bash
# email_invoice.sh
# Example script to automatically email expense reports from tpg_invoice.
#
# Copyright 2018 Michael Farrell <micolous+git@gmail.com>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

## Email address to send reports to
ADDR="example@localhost.localdomain"

## Example for use with Concur
#ADDR="receipts@concur.com"

## Subject line for the report.
SUBJECT="TPG Invoice: `date`"

## Path to tpg.secrets (your login credentials)
SECRETS="~/.config/tpg.secrets"

## You shouldn't need to change anything below this line.
REPORT="`tempfile -s .html`"
tpg_invoice -s "${SECRETS}" get --latest > $REPORT

# Does the file have any data in it?
if [ -s $REPORT ]; then
  # Wrap lines and mail report
  fmt $REPORT | mail -s "${SUBJECT}" -a 'Content-Type: text/html; charset="utf-8"' -- $ADDR
else
  echo "Error getting invoice!"
  exit 1
fi
