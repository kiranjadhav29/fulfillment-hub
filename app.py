import streamlit as st
import pandas as pd
import altair as alt
import json
import os
from datetime import datetime, timedelta
import random

st.set_page_config(
    page_title="XYZ Fulfillment Hub",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded",
)

DATA_FILE = "data.json"

# ============================================================
# STYLING — theme aware (works in light AND dark mode)
# ============================================================
st.markdown("""
<style>
    .block-container { padding-top: 1.5rem; padding-bottom: 2rem; }

    .kpi-card {
        background: var(--secondary-background-color);
        border: 1px solid rgba(128,128,128,0.25);
        border-radius: 12px;
        padding: 18px 20px;
    }
    .kpi-label {
        color: var(--text-color); opacity: 0.7;
        font-size: 0.82rem; font-weight: 600;
        text-transform: uppercase; letter-spacing: 0.05em; margin: 0;
    }
    .kpi-value {
        color: var(--text-color);
        font-size: 1.9rem; font-weight: 700;
        margin: 4px 0 0 0; line-height: 1.1;
    }
    .kpi-sub {
        color: var(--text-color); opacity: 0.6;
        font-size: 0.8rem; margin: 4px 0 0 0;
    }
    .kpi-alert { border-left: 4px solid #EF4444; }
    .kpi-warn  { border-left: 4px solid #F59E0B; }
    .kpi-good  { border-left: 4px solid #10B981; }
    .kpi-info  { border-left: 4px solid #2563EB; }

    .pill {
        display: inline-block;
        padding: 2px 10px;
        border-radius: 999px;
        font-size: 0.72rem;
        font-weight: 600;
    }
    .pill-new      { background:#DBEAFE; color:#1E40AF; }
    .pill-proc     { background:#FEF3C7; color:#92400E; }
    .pill-pick     { background:#FFEDD5; color:#9A3412; }
    .pill-pack     { background:#EDE9FE; color:#5B21B6; }
    .pill-stage    { background:#D1FAE5; color:#065F46; }
    .pill-ship     { background:#E5E7EB; color:#374151; }
    .pill-priority { background:#FEE2E2; color:#991B1B; }

    .section-title {
        font-size: 1.15rem; font-weight: 700;
        color: var(--text-color);
        margin: 1.2rem 0 0.6rem 0; padding-bottom: 6px;
        border-bottom: 2px solid rgba(128,128,128,0.25);
    }

    .order-row {
        background: var(--secondary-background-color);
        border: 1px solid rgba(128,128,128,0.25);
        border-radius: 8px;
        padding: 10px 14px; margin-bottom: 6px;
        display: flex; justify-content: space-between; align-items: center;
        color: var(--text-color);
    }
    .order-row-priority { border-left: 4px solid #EF4444; }
    .order-id {
        font-family: monospace; font-weight: 700;
        color: var(--text-color);
    }

    .pipeline-card {
        background: var(--secondary-background-color);
        border: 1px solid rgba(128,128,128,0.25);
        border-radius: 6px;
        padding: 4px 8px; margin-bottom: 4px;
        font-family: monospace; font-size: 0.8rem;
        color: var(--text-color);
    }

    div[data-testid="stMetricValue"] { font-size: 1.6rem; }
    .stButton>button { border-radius: 8px; font-weight: 600; }
</style>
""", unsafe_allow_html=True)


# ============================================================
# DATA
# ============================================================
def generate_sample_data():
    random.seed(42)
    products = [
        {"sku": "TS-RED-S",   "name": "T-Shirt Red",  "variant": "S",     "shelf": "A1"},
        {"sku": "TS-RED-M",   "name": "T-Shirt Red",  "variant": "M",     "shelf": "A1"},
        {"sku": "TS-RED-L",   "name": "T-Shirt Red",  "variant": "L",     "shelf": "A1"},
        {"sku": "TS-BLU-S",   "name": "T-Shirt Blue", "variant": "S",     "shelf": "A2"},
        {"sku": "TS-BLU-M",   "name": "T-Shirt Blue", "variant": "M",     "shelf": "A2"},
        {"sku": "TS-BLU-L",   "name": "T-Shirt Blue", "variant": "L",     "shelf": "A2"},
        {"sku": "HD-BLK-M",   "name": "Hoodie Black", "variant": "M",     "shelf": "B1"},
        {"sku": "HD-BLK-L",   "name": "Hoodie Black", "variant": "L",     "shelf": "B1"},
        {"sku": "HD-GRY-L",   "name": "Hoodie Grey",  "variant": "L",     "shelf": "B1"},
        {"sku": "CAP-WHT",    "name": "Cap",          "variant": "White", "shelf": "B2"},
        {"sku": "CAP-BLK",    "name": "Cap",          "variant": "Black", "shelf": "B2"},
        {"sku": "MUG-WHT",    "name": "Mug",          "variant": "White", "shelf": "C1"},
        {"sku": "MUG-BLK",    "name": "Mug",          "variant": "Black", "shelf": "C1"},
        {"sku": "BTL-STL-1L", "name": "Steel Bottle", "variant": "1L",    "shelf": "C2"},
        {"sku": "BAG-CNV",    "name": "Canvas Bag",   "variant": "OS",    "shelf": "C3"},
        {"sku": "SOCK-WHT-M", "name": "Socks",        "variant": "M",     "shelf": "D1"},
        {"sku": "SOCK-WHT-L", "name": "Socks",        "variant": "L",     "shelf": "D1"},
    ]

    couriers = [
        {"name": "Bluedart",    "cost": 85, "days": 2, "pickup": "14:00", "reliability": 98},
        {"name": "Delhivery",   "cost": 60, "days": 3, "pickup": "16:00", "reliability": 95},
        {"name": "India Post",  "cost": 40, "days": 5, "pickup": "11:00", "reliability": 88},
        {"name": "Ecom Express","cost": 55, "days": 3, "pickup": "17:00", "reliability": 93},
    ]

    inventory = []
    for p in products:
        inventory.append({
            "sku": p["sku"], "name": p["name"], "variant": p["variant"],
            "shelf": p["shelf"],
            "main": random.randint(0, 45),
            "second": random.randint(0, 80),
            "reorder_level": 10,
        })

    statuses = ["New", "Processing", "Picking", "Packing", "Staged", "Shipped"]
    now = datetime.now()
    orders = []
    for i in range(1, 71):
        priority = random.random() < 0.22
        status = random.choice(statuses)
        created = now - timedelta(hours=random.randint(1, 80))
        items = []
        for _ in range(random.randint(1, 3)):
            p = random.choice(products)
            items.append({"sku": p["sku"], "name": p["name"],
                          "variant": p["variant"], "shelf": p["shelf"],
                          "qty": random.randint(1, 2)})
        courier = random.choice(couriers)["name"] if status in ["Staged", "Shipped"] else None
        orders.append({
            "id": f"ORD-{1000+i}",
            "customer": f"Customer {i}",
            "priority": priority,
            "status": status,
            "created_at": created.isoformat(),
            "last_updated": created.isoformat(),
            "items": items,
            "courier": courier,
            "notes": "",
        })

    return {"products": products, "couriers": couriers,
            "inventory": inventory, "orders": orders}


def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE) as f:
            return json.load(f)
    data = generate_sample_data()
    save_data(data)
    return data


def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)


STATUS_FLOW = ["New", "Processing", "Picking", "Packing", "Staged", "Shipped"]
STATUS_EMOJI = {"New": "🔵", "Processing": "🟡", "Picking": "🟠",
                "Packing": "🟣", "Staged": "🟢", "Shipped": "⚫"}
STATUS_PILL = {"New": "pill-new", "Processing": "pill-proc",
               "Picking": "pill-pick", "Packing": "pill-pack",
               "Staged": "pill-stage", "Shipped": "pill-ship"}
STATUS_COLOR = {
    "New": "#3B82F6", "Processing": "#F59E0B", "Picking": "#F97316",
    "Packing": "#8B5CF6", "Staged": "#10B981", "Shipped": "#6B7280",
}


def find_inventory(data, sku):
    return next((i for i in data["inventory"] if i["sku"] == sku), None)


def pill(status):
    return f'<span class="pill {STATUS_PILL[status]}">{status}</span>'


def kpi(label, value, sub, kind="info"):
    return f"""
    <div class="kpi-card kpi-{kind}">
        <p class="kpi-label">{label}</p>
        <p class="kpi-value">{value}</p>
        <p class="kpi-sub">{sub}</p>
    </div>
    """


# ============================================================
# APP
# ============================================================
st.title("📦 XYZ Fulfillment Hub")
st.caption("One live view of every order, every stock item, every delay.")

data = load_data()

with st.sidebar:
    st.markdown("### 📦 Fulfillment Hub")
    st.caption("Operations Console")
    st.markdown("---")
    page = st.radio("Navigate", [
        "🏠 Dashboard",
        "📊 Analytics",
        "📋 Order Detail",
        "🧾 Picking List",
        "📦 Inventory",
        "🚚 Couriers",
        "⚠️ Delays",
    ], label_visibility="collapsed")
    st.markdown("---")
    st.caption(f"Loaded {len(data['orders'])} orders · {len(data['inventory'])} SKUs")
    if st.button("🔄 Reset demo data", use_container_width=True):
        if os.path.exists(DATA_FILE):
            os.remove(DATA_FILE)
        st.rerun()


# ============================================================
# DASHBOARD
# ============================================================
if page == "🏠 Dashboard":
    st.markdown("### Today at a glance")

    orders = data["orders"]
    total = len(orders)
    priority_pending = sum(1 for o in orders if o["priority"] and o["status"] != "Shipped")
    in_progress = sum(1 for o in orders if o["status"] != "Shipped")
    shipped = sum(1 for o in orders if o["status"] == "Shipped")

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(kpi("Total Orders", total, "Loaded today", "info"), unsafe_allow_html=True)
    with c2:
        st.markdown(kpi("Priority Pending", priority_pending, "Ship before EOD",
                        "alert" if priority_pending else "good"), unsafe_allow_html=True)
    with c3:
        st.markdown(kpi("In Progress", in_progress, "Across all stages", "warn"),
                    unsafe_allow_html=True)
    with c4:
        st.markdown(kpi("Shipped", shipped, f"{int(shipped/total*100)}% of today", "good"),
                    unsafe_allow_html=True)

    st.markdown('<p class="section-title">🚨 Priority Orders — Handle First</p>',
                unsafe_allow_html=True)
    po = [o for o in orders if o["priority"] and o["status"] != "Shipped"]
    po.sort(key=lambda x: x["created_at"])
    if not po:
        st.success("No priority orders pending ✅")
    else:
        for o in po[:6]:
            st.markdown(
                f'<div class="order-row order-row-priority">'
                f'<span class="order-id">{o["id"]}</span>'
                f'<span>{o["customer"]}</span>'
                f'<span>{pill(o["status"])}</span>'
                f'<span style="opacity:0.7;font-size:0.85rem;">created {o["created_at"][11:16]}</span>'
                f'</div>',
                unsafe_allow_html=True,
            )

    st.markdown('<p class="section-title">📊 Order Pipeline</p>', unsafe_allow_html=True)
    cols = st.columns(len(STATUS_FLOW))
    for idx, status in enumerate(STATUS_FLOW):
        with cols[idx]:
            count = sum(1 for o in orders if o["status"] == status)
            st.markdown(
                f'<div style="text-align:center;padding:8px;'
                f'background:{STATUS_COLOR[status]}22;'
                f'border-radius:8px;border-top:3px solid {STATUS_COLOR[status]};'
                f'margin-bottom:8px;">'
                f'<div style="font-size:0.75rem;opacity:0.7;font-weight:600;'
                f'text-transform:uppercase;color:var(--text-color);">'
                f'{STATUS_EMOJI[status]} {status}</div>'
                f'<div style="font-size:1.4rem;font-weight:700;'
                f'color:{STATUS_COLOR[status]};">{count}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )
            for o in [x for x in orders if x["status"] == status][:10]:
                flag = "🔴 " if o["priority"] else ""
                st.markdown(
                    f'<div class="pipeline-card">{flag}{o["id"]}</div>',
                    unsafe_allow_html=True,
                )


# ============================================================
# ANALYTICS
# ============================================================
elif page == "📊 Analytics":
    st.markdown("### Operations Analytics")

    orders = data["orders"]
    inv = pd.DataFrame(data["inventory"])

    col1, col2 = st.columns(2)

    with col1:
        st.markdown('<p class="section-title">Order Status Breakdown</p>',
                    unsafe_allow_html=True)
        status_counts = pd.DataFrame(
            [(s, sum(1 for o in orders if o["status"] == s)) for s in STATUS_FLOW],
            columns=["Status", "Orders"]
        )
        pie = alt.Chart(status_counts).mark_arc(innerRadius=60).encode(
            theta=alt.Theta("Orders:Q"),
            color=alt.Color("Status:N",
                            scale=alt.Scale(domain=STATUS_FLOW,
                                            range=[STATUS_COLOR[s] for s in STATUS_FLOW]),
                            legend=alt.Legend(orient="right", title=None)),
            tooltip=["Status", "Orders"]
        ).properties(height=320)
        st.altair_chart(pie, use_container_width=True)

    with col2:
        st.markdown('<p class="section-title">Priority vs Regular</p>',
                    unsafe_allow_html=True)
        pr = pd.DataFrame([
            ("Priority", sum(1 for o in orders if o["priority"])),
            ("Regular",  sum(1 for o in orders if not o["priority"])),
        ], columns=["Type", "Count"])
        bar = alt.Chart(pr).mark_bar(cornerRadiusTopLeft=6, cornerRadiusTopRight=6).encode(
            x=alt.X("Type:N", axis=alt.Axis(labelAngle=0, title=None)),
            y=alt.Y("Count:Q", title="Orders"),
            color=alt.Color("Type:N",
                            scale=alt.Scale(domain=["Priority", "Regular"],
                                            range=["#EF4444", "#3B82F6"]),
                            legend=None),
            tooltip=["Type", "Count"]
        ).properties(height=320)
        st.altair_chart(bar, use_container_width=True)

    col3, col4 = st.columns(2)

    with col3:
        st.markdown('<p class="section-title">Stock: Main vs Second Warehouse</p>',
                    unsafe_allow_html=True)
        total_main = int(inv["main"].sum())
        total_second = int(inv["second"].sum())
        wh = pd.DataFrame([
            ("Main Warehouse", total_main),
            ("Second Warehouse", total_second),
        ], columns=["Warehouse", "Units"])
        donut = alt.Chart(wh).mark_arc(innerRadius=60).encode(
            theta="Units:Q",
            color=alt.Color("Warehouse:N",
                            scale=alt.Scale(domain=["Main Warehouse", "Second Warehouse"],
                                            range=["#10B981", "#F59E0B"]),
                            legend=alt.Legend(orient="right", title=None)),
            tooltip=["Warehouse", "Units"]
        ).properties(height=320)
        st.altair_chart(donut, use_container_width=True)
        st.caption(f"Main: **{total_main}** units · Second: **{total_second}** units")

    with col4:
        st.markdown('<p class="section-title">Top 8 SKUs by Stock</p>',
                    unsafe_allow_html=True)
        inv["total"] = inv["main"] + inv["second"]
        top = inv.nlargest(8, "total")[["sku", "total"]]
        barh = alt.Chart(top).mark_bar(cornerRadiusTopRight=6, cornerRadiusBottomRight=6).encode(
            y=alt.Y("sku:N", sort="-x", title=None),
            x=alt.X("total:Q", title="Units"),
            color=alt.value("#2563EB"),
            tooltip=["sku", "total"]
        ).properties(height=320)
        st.altair_chart(barh, use_container_width=True)

    st.markdown('<p class="section-title">Courier Comparison — Cost vs Speed</p>',
                unsafe_allow_html=True)
    cdf = pd.DataFrame(data["couriers"])
    cdf["reliability"] = cdf["reliability"].astype(float)
    scatter = alt.Chart(cdf).mark_circle(size=400, opacity=0.75).encode(
        x=alt.X("cost:Q", title="Cost (₹)"),
        y=alt.Y("days:Q", title="Delivery Days", scale=alt.Scale(reverse=True)),
        color=alt.Color("name:N", legend=alt.Legend(title="Courier", orient="right")),
        tooltip=["name", "cost", "days", "pickup", "reliability"]
    ).properties(height=300)
    text = scatter.mark_text(dy=-18, fontSize=11).encode(text="name:N")
    st.altair_chart(scatter + text, use_container_width=True)
    st.caption("Bottom-left = best (cheap + fast). Top-right = expensive + slow.")


# ============================================================
# ORDER DETAIL
# ============================================================
elif page == "📋 Order Detail":
    st.markdown("### Order Detail")

    selected = st.selectbox("Select Order", [o["id"] for o in data["orders"]])
    order = next(o for o in data["orders"] if o["id"] == selected)

    col1, col2 = st.columns([2, 1])

    with col1:
        if order["priority"]:
            st.error("🔴 **PRIORITY ORDER** — must ship same day")
        st.markdown(f"#### {order['id']} · {order['customer']}")
        c1, c2, c3 = st.columns(3)
        c1.markdown(f"**Status**<br>{pill(order['status'])}", unsafe_allow_html=True)
        c2.markdown(f"**Created**<br>`{order['created_at'][:16].replace('T',' ')}`")
        c3.markdown(f"**Courier**<br>{order['courier'] or '— not assigned —'}")

        st.markdown('<p class="section-title">Items to pick</p>', unsafe_allow_html=True)
        rows = []
        for it in order["items"]:
            inv = find_inventory(data, it["sku"])
            main = inv["main"] if inv else 0
            second = inv["second"] if inv else 0
            if main >= it["qty"]:
                flag = "✅ In main warehouse"
            elif second >= it["qty"]:
                flag = "⚠️ Move from 2nd warehouse"
            else:
                flag = "❌ Out of stock"
            rows.append({
                "SKU": it["sku"], "Product": it["name"], "Variant": it["variant"],
                "Shelf": it["shelf"], "Qty": it["qty"],
                "Main": main, "2nd": second, "Status": flag,
            })
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    with col2:
        st.markdown('<p class="section-title">Actions</p>', unsafe_allow_html=True)

        idx = STATUS_FLOW.index(order["status"])
        st.markdown("**Workflow**")
        for i, s in enumerate(STATUS_FLOW):
            marker = "🟢" if i < idx else ("🔵" if i == idx else "⚪")
            weight = "700" if i == idx else "400"
            st.markdown(f"{marker} <span style='font-weight:{weight};'>{s}</span>",
                        unsafe_allow_html=True)

        st.markdown("")
        if idx < len(STATUS_FLOW) - 1:
            nxt = STATUS_FLOW[idx + 1]
            if st.button(f"➡️ Move to {nxt}", use_container_width=True, type="primary"):
                order["status"] = nxt
                order["last_updated"] = datetime.now().isoformat()
                save_data(data)
                st.rerun()

        if order["status"] in ["Packing", "Staged"] and not order["courier"]:
            courier = st.selectbox("Assign courier",
                                   [c["name"] for c in data["couriers"]])
            if st.button("📮 Assign courier", use_container_width=True):
                order["courier"] = courier
                save_data(data)
                st.rerun()

        note = st.text_area("Internal notes", value=order.get("notes", ""), height=80)
        if st.button("💾 Save note", use_container_width=True):
            order["notes"] = note
            save_data(data)
            st.success("Saved")


# ============================================================
# PICKING LIST
# ============================================================
elif page == "🧾 Picking List":
    st.markdown("### 🧾 Picking List — Warehouse Copy")
    st.caption("Priority first. Print and hand to picker. Big rows, clear shelves.")

    pending = [o for o in data["orders"]
               if o["status"] in ["New", "Processing", "Picking"]]
    pending.sort(key=lambda x: (not x["priority"], x["created_at"]))

    if not pending:
        st.info("No orders to pick right now 🎉")
    else:
        col1, col2, col3 = st.columns(3)
        col1.metric("Total to pick", len(pending))
        col2.metric("Priority", sum(1 for o in pending if o["priority"]))
        col3.metric("Regular", sum(1 for o in pending if not o["priority"]))

        for o in pending[:25]:
            tag = "🔴 PRIORITY" if o["priority"] else "⚪ Regular"
            with st.expander(f"{tag}  |  {o['id']}  |  {o['customer']}"):
                rows = []
                for it in o["items"]:
                    inv = find_inventory(data, it["sku"])
                    main = inv["main"] if inv else 0
                    rows.append({
                        "Pick?": "☐", "Shelf": it["shelf"],
                        "Product": it["name"], "Variant": it["variant"],
                        "Qty": it["qty"], "In Main": main,
                        "Move 2nd?": "YES ⚠️" if main < it["qty"] else "—",
                    })
                st.table(pd.DataFrame(rows))


# ============================================================
# INVENTORY
# ============================================================
elif page == "📦 Inventory":
    st.markdown("### 📦 Inventory — Main vs Second Warehouse")

    inv_df = pd.DataFrame(data["inventory"])
    inv_df["total"] = inv_df["main"] + inv_df["second"]
    inv_df["low_stock"] = inv_df["main"] < inv_df["reorder_level"]

    c1, c2, c3, c4 = st.columns(4)
    c1.markdown(kpi("SKUs Tracked", len(inv_df), "Total products", "info"),
                unsafe_allow_html=True)
    c2.markdown(kpi("Units in Main", int(inv_df["main"].sum()), "Ready to pick", "good"),
                unsafe_allow_html=True)
    c3.markdown(kpi("Units in 2nd", int(inv_df["second"].sum()), "Overflow stock", "warn"),
                unsafe_allow_html=True)
    c4.markdown(kpi("Low Stock SKUs", int(inv_df["low_stock"].sum()), "Main < reorder", "alert"),
                unsafe_allow_html=True)

    st.markdown('<p class="section-title">Full Inventory</p>', unsafe_allow_html=True)
    view = inv_df[["sku", "name", "variant", "shelf",
                   "main", "second", "total", "low_stock"]].rename(columns={
        "sku": "SKU", "name": "Product", "variant": "Variant",
        "shelf": "Shelf", "main": "Main WH", "second": "2nd WH",
        "total": "Total", "low_stock": "Low?"
    })
    st.dataframe(view, use_container_width=True, hide_index=True)

    colA, colB = st.columns([1, 1])

    with colA:
        st.markdown('<p class="section-title">🔁 Move stock: Second ➡️ Main</p>',
                    unsafe_allow_html=True)
        sku = st.selectbox("SKU", inv_df["sku"].tolist())
        qty = st.number_input("Qty to move", min_value=1, max_value=200, value=10)
        if st.button("📦 Move stock", use_container_width=True, type="primary"):
            inv = find_inventory(data, sku)
            if inv["second"] >= qty:
                inv["second"] -= qty
                inv["main"] += qty
                save_data(data)
                st.success(f"Moved {qty} × {sku} → Main")
                st.rerun()
            else:
                st.error(f"Only {inv['second']} units in Second warehouse.")

    with colB:
        st.markdown('<p class="section-title">🚨 Low Stock (Main < 10)</p>',
                    unsafe_allow_html=True)
        low = view[view["Low?"]]
        if low.empty:
            st.success("All items healthy in main warehouse.")
        else:
            st.dataframe(low, use_container_width=True, hide_index=True)


# ============================================================
# COURIERS
# ============================================================
elif page == "🚚 Couriers":
    st.markdown("### 🚚 Courier Options")
    st.caption("Choose the cheapest courier that still meets the delivery promise.")

    cdf = pd.DataFrame(data["couriers"])
    cdf["reliability"] = cdf["reliability"].astype(float)

    c1, c2, c3 = st.columns(3)
    cheapest = cdf.loc[cdf["cost"].idxmin()]
    fastest = cdf.loc[cdf["days"].idxmin()]
    most_reliable = cdf.loc[cdf["reliability"].idxmax()]
    c1.markdown(kpi("Cheapest", cheapest["name"],
                    f"₹{int(cheapest['cost'])} · {int(cheapest['days'])} days", "good"),
                unsafe_allow_html=True)
    c2.markdown(kpi("Fastest", fastest["name"],
                    f"{int(fastest['days'])} days · ₹{int(fastest['cost'])}", "info"),
                unsafe_allow_html=True)
    c3.markdown(kpi("Most Reliable", most_reliable["name"],
                    f"{int(most_reliable['reliability'])}% on-time", "good"),
                unsafe_allow_html=True)

    st.markdown('<p class="section-title">All Couriers</p>', unsafe_allow_html=True)
    display = cdf.rename(columns={
        "name": "Courier", "cost": "Cost (₹)", "days": "Days",
        "pickup": "Pickup", "reliability": "Reliability (%)"
    })
    st.dataframe(display, use_container_width=True, hide_index=True)

    st.markdown('<p class="section-title">Cost vs Delivery Days</p>', unsafe_allow_html=True)
    chart = alt.Chart(cdf).mark_bar(cornerRadiusTopLeft=6, cornerRadiusTopRight=6).encode(
        x=alt.X("name:N", title=None, axis=alt.Axis(labelAngle=0)),
        y=alt.Y("cost:Q", title="Cost (₹)"),
        color=alt.Color("days:Q", title="Days",
                        scale=alt.Scale(scheme="redyellowgreen", reverse=True)),
        tooltip=["name", "cost", "days", "pickup", "reliability"]
    ).properties(height=300)
    st.altair_chart(chart, use_container_width=True)


# ============================================================
# DELAYS
# ============================================================
elif page == "⚠️ Delays":
    st.markdown("### ⚠️ Delayed / At-Risk Orders")
    st.caption("Any unshipped order older than 12 hours is flagged.")

    now = datetime.now()
    delays = []
    for o in data["orders"]:
        if o["status"] == "Shipped":
            continue
        age = (now - datetime.fromisoformat(o["created_at"])).total_seconds() / 3600
        if age > 12:
            delays.append({
                "Order": o["id"],
                "Priority": "🔴 YES" if o["priority"] else "—",
                "Status": o["status"],
                "Age (hrs)": round(age, 1),
                "Customer": o["customer"],
            })

    if not delays:
        st.success("No delayed orders ✅")
    else:
        c1, c2, c3 = st.columns(3)
        c1.markdown(kpi("Delayed Orders", len(delays), "Need attention", "alert"),
                    unsafe_allow_html=True)
        c2.markdown(kpi("Priority Delayed",
                        sum(1 for d in delays if "YES" in d["Priority"]),
                        "Critical", "alert"), unsafe_allow_html=True)
        c3.markdown(kpi("Oldest", f"{max(d['Age (hrs)'] for d in delays)}h",
                        "Since creation", "warn"), unsafe_allow_html=True)

        st.markdown('<p class="section-title">Delayed Orders</p>', unsafe_allow_html=True)
        ddf = pd.DataFrame(delays).sort_values("Age (hrs)", ascending=False)
        st.dataframe(ddf, use_container_width=True, hide_index=True)

        st.markdown('<p class="section-title">Delay Distribution by Status</p>',
                    unsafe_allow_html=True)
        hist = alt.Chart(ddf).mark_bar(cornerRadiusTopLeft=6, cornerRadiusTopRight=6).encode(
            x=alt.X("Status:N", title=None, axis=alt.Axis(labelAngle=0)),
            y=alt.Y("count():Q", title="Orders"),
            color=alt.Color("Status:N",
                            scale=alt.Scale(domain=STATUS_FLOW,
                                            range=[STATUS_COLOR[s] for s in STATUS_FLOW]),
                            legend=None),
            tooltip=["Status", "count()"]
        ).properties(height=280)
        st.altair_chart(hist, use_container_width=True)