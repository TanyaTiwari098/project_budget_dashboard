import streamlit as st
from supabase import create_client, Client
import pandas as pd
from datetime import datetime

# --- Supabase Configuration ---
url = "https://orcofktzjrbbjczcqqrg.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im9yY29ma3R6anJiYmpjemNxcXJnIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDgzMjMxOTUsImV4cCI6MjA2Mzg5OTE5NX0.V2lxi3pZZzPuUX3uUjt8I1ZML_uLTbkDFDTxvcEbQ9I"
supabase: Client = create_client(url, key)

st.set_page_config(page_title="Project Budget Dashboard", layout="wide")
st.title("📊 Project Budget & Cash Flow Dashboard")

# --- Add New Project ---
with st.expander("➕ Add New Project"):
    with st.form("project_form"):
        lead = st.text_input("Lead Name")
        name = st.text_input("Project Name")
        start_date = st.date_input("Start Date")
        end_date = st.date_input("End Date")
        budget = st.number_input("Budget", min_value=0.0, step=100.0)
        submitted = st.form_submit_button("Add Project")
        if submitted:
            supabase.table("projects").insert({
                "lead": lead,
                "name": name,
                "start_date": str(start_date),
                "end_date": str(end_date),
                "budget": budget,
                "created_at": datetime.utcnow().isoformat()
            }).execute()
            st.success("✅ Project Added")

# --- Load Projects ---
projects_data = supabase.table("projects").select("*").execute().data
if not projects_data:
    st.warning("⚠️ No projects found. Add one above.")
    st.stop()

df_projects = pd.DataFrame(projects_data)
selected = st.selectbox("Select a Project", df_projects["name"])
project = df_projects[df_projects["name"] == selected].iloc[0]
st.subheader(f"📁 Project: {project['name']}")
st.write(f"Lead: {project['lead']} | Start: {project['start_date']} | End: {project['end_date']} | Budget: ${project['budget']:,.2f}")

# --- Collections Module ---
collections = supabase.table("collections").select("*").eq("project_id", project["id"]).execute().data
df_collections = pd.DataFrame(collections)
st.metric("💰 Total Collections", f"${df_collections['amount'].sum():,.2f}" if not df_collections.empty else "$0")

with st.expander("➕ Add Collection"):
    with st.form("collection_form"):
        amount = st.number_input("Amount", step=100.0)
        date = st.date_input("Date")
        status = st.selectbox("Status", ["Paid", "Pending", "Late"])
        submitted = st.form_submit_button("Add")
        if submitted:
            supabase.table("collections").insert({
                "project_id": project["id"],
                "amount": amount,
                "date": str(date),
                "status": status
            }).execute()
            st.success("✅ Collection Added")

# --- Expenses Module ---
expenses = supabase.table("expenses").select("*").eq("project_id", project["id"]).execute().data
df_expenses = pd.DataFrame(expenses)
st.metric("💸 Total Expenses", f"${df_expenses['amount'].sum():,.2f}" if not df_expenses.empty else "$0")

with st.expander("➕ Add Expense / AP"):
    with st.form("expense_form"):
        amount = st.number_input("Amount", step=50.0)
        date = st.date_input("Date", value=datetime.today())
        vendor = st.text_input("Vendor / Description")
        urgency = st.selectbox("Urgency", ["Critical", "Flexible", "Optional"])
        submitted = st.form_submit_button("Add")
        if submitted:
            supabase.table("expenses").insert({
                "project_id": project["id"],
                "amount": amount,
                "date": str(date),
                "vendor": vendor,
                "urgency": urgency
            }).execute()
            st.success("✅ Expense Added")

# --- Cash Flow Forecast ---
st.subheader("🔮 Cash Flow Forecast")
cash_on_hand = st.number_input("💼 Current Cash Balance", min_value=0.0, step=100.0)
inflow = df_collections['amount'].sum() if not df_collections.empty else 0
outflow = df_expenses['amount'].sum() if not df_expenses.empty else 0
net = cash_on_hand + inflow - outflow

col1, col2, col3 = st.columns(3)
col1.metric("Projected Inflows", f"${inflow:,.2f}")
col2.metric("Projected Outflows", f"${outflow:,.2f}")
col3.metric("Projected Cash", f"${net:,.2f}", delta=f"{net - cash_on_hand:+,.2f}")

# --- Charts ---
st.subheader("📈 Visual Reports")
if not df_collections.empty:
    df_collections["date"] = pd.to_datetime(df_collections["date"])
    st.bar_chart(df_collections.set_index("date")["amount"], use_container_width=True)

if not df_expenses.empty:
    df_expenses["date"] = pd.to_datetime(df_expenses["date"])
    st.line_chart(df_expenses.set_index("date")["amount"], use_container_width=True)