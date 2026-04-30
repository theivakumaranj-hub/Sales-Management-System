import streamlit as st
import pandas as pd
import psycopg2

# --- 1. Database Connection Functions ---
def get_db_connection():
    return psycopg2.connect(
        host="localhost",
        database="sales_management",
        user="postgres", 
        password="kumaranias7" # UPDATE THIS!
    )

def get_data(query, params=None):
    try:
        conn = get_db_connection()
        df = pd.read_sql(query, conn, params=params)
        conn.close()
        return df
    except Exception as e:
        st.error(f"Database Fetch Error: {e}")
        return pd.DataFrame()

def run_transaction(query, params):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(query, params)
        conn.commit()
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        st.error(f"Transaction Error: {e}")
        return False

# --- 2. Page Configuration & Session State ---
st.set_page_config(page_title="Sales Intelligence Hub", layout="wide")
st.title("📊 Branch-Based Sales Management System")

if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
    st.session_state['role'] = None
    st.session_state['branch_id'] = None
    st.session_state['username'] = None

# --- 3. Secure Login / Logout Module ---
if not st.session_state['logged_in']:
    st.sidebar.header("System Login")
    username_input = st.sidebar.text_input("Username")
    password_input = st.sidebar.text_input("Password", type="password")
    
    if st.sidebar.button("Login"):
        auth_query = "SELECT role, branch_id FROM users WHERE username = %s AND password = %s"
        user_df = get_data(auth_query, (username_input, password_input))
        
        if not user_df.empty:
            # 1. Capture the data first
            role_val = user_df['role'].iloc[0]
            raw_branch_id = user_df['branch_id'].iloc[0]
            
            # 2. Safety Check: Only convert to int if it's NOT NULL
            if pd.isna(raw_branch_id):
                final_branch_id = None
            else:
                final_branch_id = int(raw_branch_id)
            
            # 3. Only now set the session state (prevents the "None" name error)
            st.session_state['role'] = role_val
            st.session_state['branch_id'] = final_branch_id
            st.session_state['username'] = username_input
            st.session_state['logged_in'] = True 
            
            st.rerun()
        else:
            st.sidebar.error("Invalid Username or Password")
else:
    st.sidebar.success(f"Welcome, {st.session_state['username']} ({st.session_state['role']})")
    if st.sidebar.button("Logout"):
        st.session_state['logged_in'] = False
        st.session_state['role'] = None
        st.session_state['branch_id'] = None
        st.session_state['username'] = None
        st.rerun()

# --- 4. Main Application (Protected) ---
if st.session_state['logged_in']:
    
    # Establish Role-Based Data Filtering
    role = st.session_state['role']
    user_branch_id = st.session_state['branch_id']
    
    if role == 'Super Admin':
        view_filter = "1=1" 
    else:
        view_filter = f"customer_sales.branch_id = {user_branch_id}" 
        
    # App Navigation
    tab1, tab2, tab3 = st.tabs(["📈 Dashboard & Reports", "✍️ Data Entry", "🔍 SQL Queries"])
    
    # --- TAB 1: DASHBOARD ---
    with tab1:
        st.subheader("Financial Overview")
        kpi_query = f"SELECT SUM(gross_sales) as total_sales, SUM(received_amount) as total_received, SUM(pending_amount) as total_pending FROM customer_sales WHERE {view_filter}"
        kpi_df = get_data(kpi_query)
        
        if not kpi_df.empty and pd.notna(kpi_df['total_sales'].iloc[0]):
            col1, col2, col3 = st.columns(3)
            col1.metric("Total Gross Sales", f"₹{kpi_df['total_sales'].iloc[0]:,.2f}")
            col2.metric("Total Received", f"₹{kpi_df['total_received'].iloc[0]:,.2f}")
            col3.metric("Total Pending", f"₹{kpi_df['total_pending'].iloc[0]:,.2f}")
            
        st.divider()
        st.subheader("Sales Records")
        sales_query = f"SELECT sale_id, date, customer_name, product_name, gross_sales, received_amount, pending_amount, status FROM customer_sales WHERE {view_filter} ORDER BY date DESC, sale_id DESC"
        sales_df = get_data(sales_query)
        st.dataframe(sales_df, use_container_width=True)

    # --- TAB 2: DATA ENTRY (WITH ROLE RESTRICTIONS) ---
    with tab2:
        col_form1, col_form2 = st.columns(2)
        
        # FORM 1: Add New Sale
        with col_form1:
            st.subheader("Add New Sale Entry")
            with st.form("add_sale_form", clear_on_submit=True):
                if role == 'Super Admin':
                    branches_df = get_data("SELECT branch_id, branch_name FROM branches")
                    branch_options = dict(zip(branches_df.branch_name, branches_df.branch_id))
                    selected_branch_name = st.selectbox("Select Branch", options=list(branch_options.keys()))
                    # FIX 2: Convert numpy.int64 to standard Python int for the branch dropdown
                    insert_branch_id = int(branch_options[selected_branch_name])
                else:
                    st.info(f"Adding sale for your assigned Branch ID: {user_branch_id}")
                    insert_branch_id = user_branch_id
                
                date = st.date_input("Date")
                customer_name = st.text_input("Customer Name")
                mobile_number = st.text_input("Mobile Number")
                product_name = st.selectbox("Product", ["DS", "DA", "BA", "FSD"])
                gross_sales = st.number_input("Gross Sales (₹)", min_value=0.0, format="%.2f")
                status = st.selectbox("Status", ["Open", "Close"])
                
                if st.form_submit_button("Record Sale"):
                    query = "INSERT INTO customer_sales (branch_id, date, customer_name, mobile_number, product_name, gross_sales, status) VALUES (%s, %s, %s, %s, %s, %s, %s)"
                    if run_transaction(query, (insert_branch_id, date, customer_name, mobile_number, product_name, gross_sales, status)):
                        st.success("Sale added successfully!")
                        
        # FORM 2: Add Payment Split
        with col_form2:
            st.subheader("Record Payment Split")
            with st.form("add_payment_form", clear_on_submit=True):
                allowed_sales_df = get_data(f"SELECT sale_id, customer_name FROM customer_sales WHERE {view_filter} AND status='Open'")
                
                if not allowed_sales_df.empty:
                    sale_options = {f"Sale #{row['sale_id']} - {row['customer_name']}": row['sale_id'] for _, row in allowed_sales_df.iterrows()}
                    selected_sale_label = st.selectbox("Select Active Sale", options=list(sale_options.keys()))
                    # FIX 3: Convert numpy.int64 to standard Python int for the sale ID dropdown
                    insert_sale_id = int(sale_options[selected_sale_label])
                    
                    payment_date = st.date_input("Payment Date")
                    amount_paid = st.number_input("Amount Paid (₹)", min_value=1.0, format="%.2f")
                    payment_method = st.selectbox("Payment Method", ["Cash", "UPI", "Card"])
                    
                    if st.form_submit_button("Record Payment"):
                        query = "INSERT INTO payment_splits (sale_id, payment_date, amount_paid, payment_method) VALUES (%s, %s, %s, %s)"
                        if run_transaction(query, (insert_sale_id, payment_date, amount_paid, payment_method)):
                            st.success("Payment recorded! Database triggers have updated the pending amounts.")
                else:
                    st.warning("No open sales available for payment in your assigned branches.")
                    st.form_submit_button("Record Payment", disabled=True)

    # --- TAB 3: ALL 15 PREDEFINED SQL QUERIES (SECURED) ---
    with tab3:
        st.subheader("Business Insights Hub (15 Required Queries)")
        
        queries = {
            "1. All records from customer_sales": f"SELECT * FROM customer_sales WHERE {view_filter} ORDER BY date DESC, sale_id DESC",
            "2. All records from branches": f"SELECT * FROM branches",
            "3. All records from payment_splits": f"SELECT payment_splits.* FROM payment_splits JOIN customer_sales ON payment_splits.sale_id = customer_sales.sale_id WHERE {view_filter}",
            "4. Sales with status 'Open'": f"SELECT * FROM customer_sales WHERE status = 'Open' AND {view_filter}",
            "5. Total gross sales": f"SELECT SUM(gross_sales) as Total_Gross_Sales FROM customer_sales WHERE {view_filter}",
            "6. Total received amount": f"SELECT SUM(received_amount) as Total_Received FROM customer_sales WHERE {view_filter}",
            "7. Total pending amount": f"SELECT SUM(pending_amount) as Total_Pending FROM customer_sales WHERE {view_filter}",
            "8. Total number of sales per branch": f"SELECT branch_id, COUNT(*) as Total_Sales FROM customer_sales WHERE {view_filter} GROUP BY branch_id",
            "9. Average gross sales amount": f"SELECT AVG(gross_sales) as Average_Sales FROM customer_sales WHERE {view_filter}",
            "10. Sales details with branch name": f"SELECT customer_sales.sale_id, customer_sales.customer_name, branches.branch_name FROM customer_sales JOIN branches ON customer_sales.branch_id = branches.branch_id WHERE {view_filter}",
            "11. Branch-wise total gross sales": f"SELECT branches.branch_name, SUM(customer_sales.gross_sales) as Total_Sales FROM customer_sales JOIN branches ON customer_sales.branch_id = branches.branch_id WHERE {view_filter} GROUP BY branches.branch_name",
            "12. Sales with payment method used": f"SELECT customer_sales.sale_id, customer_sales.customer_name, payment_splits.payment_method FROM customer_sales JOIN payment_splits ON customer_sales.sale_id = payment_splits.sale_id WHERE {view_filter}",
            "13. Sales with pending amount > 5000": f"SELECT * FROM customer_sales WHERE pending_amount > 5000 AND {view_filter}",
            "14. Top 3 highest gross sales": f"SELECT * FROM customer_sales WHERE {view_filter} ORDER BY gross_sales DESC LIMIT 3",
            "15. Payment method-wise total collection": f"SELECT payment_splits.payment_method, SUM(payment_splits.amount_paid) as Total_Collection FROM payment_splits JOIN customer_sales ON payment_splits.sale_id = customer_sales.sale_id WHERE {view_filter} GROUP BY payment_splits.payment_method"
        }
        
        selected_query_name = st.selectbox("Select a query to execute:", list(queries.keys()))
        
        if st.button("Run Query"):
            sql_to_run = queries[selected_query_name]
            st.code(sql_to_run, language='sql')
            
            result_df = get_data(sql_to_run)
            if not result_df.empty:
                st.dataframe(result_df, use_container_width=True)
            else:
                st.info("Query returned no results for your branch.")