# XYZ Fulfillment Hub

A single-page tool that replaces XYZ's spreadsheet + shared-folder workflow
with one live view of orders, inventory, picking, and delays.

## Problems Solved

1. **No status visibility** → Live Kanban board on the Dashboard
2. **Priority orders missed** → Priority orders flagged red and auto-sorted to top
3. **Stock missing / wrong warehouse** → Inventory page shows Main vs Second warehouse with a one-click transfer
4. **Wrong product/variant shipped** → Picking List shows SKU, variant, shelf and a tick-box
5. **Delays go unnoticed** → Delays page flags any order stuck > 12 hrs

## Stack
- Python + Streamlit
- Pandas for tables
- JSON file for storage (no DB needed for demo)

## Run Locally

```bash
pip install -r requirements.txt
streamlit run app.py