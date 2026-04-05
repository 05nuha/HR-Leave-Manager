# HR Leave Manager

A complete HR leave management module for Odoo 19, built for the Business, Finance & Workforce ERP Hackathon.

## Overview

HR Leave Manager gives organisations full control over employee leave — from initial request to final approval. It features a real-time dashboard, multi-view analytics, automated workflows, and printable leave documents.

## Features

- **Live Dashboard** — at-a-glance overview of all leave activity with clickable stat cards showing draft, pending, approved, and refused counts with percentage breakdowns
- **Leave Requests** — full approval workflow (Draft → Submitted → Approved/Refused) with email notifications and chatter tracking on every state change
- **Multiple Views** — list, kanban, calendar, graph, and pivot views for leave requests
- **Overlap Validation** — automatically prevents employees from submitting overlapping leave requests
- **Allocations** — manage leave entitlements per employee per leave type with remaining days calculated in real time
- **Leave Types** — configurable leave types with color coding, max days, and approval settings (Annual, Sick, Emergency, Maternity, Study included)
- **PDF Reports** — print professional leave request documents with employee details, leave period, reason, and signature fields
- **Automated Cron Job** — daily scheduled action that automatically refuses expired pending requests

## Installation

1. Clone this repository into your Odoo addons folder:
   ```bash
   git clone https://github.com/05nuha/HR-Leave-Manager.git
   ```
2. Add the folder path to your `addons_path` in `odoo.conf`
3. Restart the Odoo server
4. Go to Apps, search for **HR Leave Manager** and click Install

## Requirements

- Odoo 19
- Python 3.10+
- `base` and `mail` modules (included with Odoo)
- wkhtmltopdf (optional, for PDF export)

## Author

Nuha Aburamadan
