import streamlit as st
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from scipy.optimize import fsolve

# ==========================================
# 0. CONFIGURATION & ACCESS CONTROL
# ==========================================
st.set_page_config(page_title="VAYU TARAL - Gas Dynamics", layout="wide")

# Set the license key required to access the platform
# In production, set st.secrets["ACCESS_KEY"]
VALID_LICENSE_KEY = "jnagpal@vayu.com"

def authenticate_user():
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False

    if not st.session_state["authenticated"]:
        st.title("🚀 VAYU TARAL: Gas Dynamics Engine")
        st.subheader("Module 01 - Conceptual Design Suite")
        st.info("🔒 Restricted Access: Enterprise Authentication Required")
        
        user_key = st.text_input("Enter License Key / Access Token", type="password")
        if st.button("Unlock Module 01"):
            if user_key == VALID_LICENSE_KEY:
                st.session_state["authenticated"] = True
                st.rerun()
            else:
                st.error("❌ Access Denied: Invalid License Token.")
        return False
    return True

# If unauthenticated, stop execution here
if not authenticate_user():
    st.stop()

# Logout button in sidebar
if st.sidebar.button("🔒 Lock Suite"):
    st.session_state["authenticated"] = False
    st.rerun()

# ==========================================
# 1. BHAUTIKYA & GANITYA ENGINE (Physics Core)
# ==========================================
def area_mach_relation(M, g=1.4):
    if M == 0: return np.inf
    term = (2 / (g + 1)) * (1 + (g - 1) / 2 * M**2)
    return (1 / M) * (term)**((g + 1) / (2 * (g - 1)))

def solve_mach_from_area(area_ratio, g=1.4, regime='subsonic'):
    func = lambda M: area_mach_relation(M, g) - area_ratio
    guess = 0.3 if regime == 'subsonic' else 2.5
    return fsolve(func, guess)[0]

def get_static_p(p0, M, g=1.4):
    return p0 * (1 + (g - 1) / 2 * M**2)**(-g / (g - 1))

def get_fanno_lmax_ratio(M, g=1.4):
    term1 = (1 - M**2) / (g * M**2)
    term2 = ((g + 1) / (2 * g)) * np.log(((g + 1) * M**2) / (2 + (g - 1) * M**2))
    return term1 + term2

def fanno_property_ratios(M, g=1.4):
    p_ps = (1 / M) * np.sqrt((g + 1) / (2 + (g - 1) * M**2))
    rho_rhos = (1 / M) * np.sqrt((2 + (g - 1) * M**2) / (g + 1))
    p0_p0s = (1 / M) * ((2 + (g - 1) * M**2) / (g + 1))**((g + 1) / (2 * (g - 1)))
    t_ts = (g + 1) / (2 + (g - 1) * M**2)
    return p_ps, rho_rhos, p0_p0s, t_ts

def rayleigh_ratios(M, g=1.4):
    t0_t0s = (2*(g+1)*M**2 * (1+(g-1)/2*M**2)) / (1+g*M**2)**2
    p_ps = (1+g) / (1+g*M**2)
    rho_rhos = (1/M**2) * ((1+g*M**2)/(1+g))
    p0_p0s = ((1+g)/(1+g*M**2)) * ((1+(g-1)/2*M**2)/((g+1)/2))**(g/(g-1))
    return t0_t0s, p_ps, rho_rhos, p0_p0s

def solve_m2_fanno(target_lmax, m1, g=1.4):
    search_guess = 0.8 if m1 < 1 else 1.2
    func = lambda M: get_fanno_lmax_ratio(M, g) - target_lmax
    return fsolve(func, search_guess)[0]

def solve_m2_rayleigh(target_ratio, m1, g=1.4):
    search_guess = 0.5 if m1 < 1 else 1.5
    func = lambda M: rayleigh_ratios(M, g)[0] - target_ratio
    return fsolve(func, search_guess)[0]

# ==========================================
# 2. APP ROUTING & UI LAYOUT
# ==========================================
st.sidebar.title("VAYU TARAL 🚀")
st.sidebar.markdown("**Module 01: Gas Dynamics (GD)**")

selected_submodule = st.sidebar.radio(
    "Select Solver Routine:",
    ["GD02-F: Fanno Flow Analysis",
     "GD02-R: Rayleigh Flow Analysis",
     "GD05-Sub: Subsonic Nozzle Flow",
     "GD05-Sup: Supersonic C-D Nozzle Flow"]
)

# ------------------------------------------
# ROUTINE 1: FANNO FLOW
# ------------------------------------------
if selected_submodule == "GD02-F: Fanno Flow Analysis":
    st.title("Vayu Taral: Fanno Flow Solver (GD02-F)")
    
    with st.sidebar:
        st.header("MIMO Inputs")
        m1 = st.slider("Upstream Mach (M1)", 0.1, 3.5, 0.6)
        f = st.number_input("Friction Factor (f)", value=0.005, format="%.4f")
        L = st.number_input("Duct Length (L) [m]", value=2.0)
        D = st.number_input("Duct Diameter (D) [m]", value=0.1)
        gamma = 1.4

    lmax1_ratio = get_fanno_lmax_ratio(m1, gamma)
    delta_l_ratio = (4 * f * L) / D
    lmax2_ratio = lmax1_ratio - delta_l_ratio

    if lmax2_ratio < 0:
        st.error(f"❌ FRICTIONAL CHOKING: Duct length L={L}m exceeds Lmax={ (lmax1_ratio*D)/(4*f) :.2f}m.")
        m2 = 1.0
    else:
        m2 = solve_m2_fanno(lmax2_ratio, m1, gamma)

    fig = make_subplots(rows=2, cols=2, subplot_titles=("Static Temperature (T/T*)", "Static Pressure (P/P*)", 
                                                        "Density (Rho/Rho*)", "Stagnation Pressure Loss (P0/P0*)"))
    m_range = np.linspace(0.1, 3.5, 500)
    p_r, r_r, p0_r, t_r = fanno_property_ratios(m_range, gamma)

    fig.add_trace(go.Scatter(x=m_range, y=t_r, name="T/T*"), row=1, col=1)
    fig.add_trace(go.Scatter(x=m_range, y=p_r, name="P/P*"), row=1, col=2)
    fig.add_trace(go.Scatter(x=m_range, y=r_r, name="Rho/Rho*"), row=2, col=1)
    fig.add_trace(go.Scatter(x=m_range, y=p0_r, name="P0/P0*"), row=2, col=2)

    p_1, r_1, p0_1, t_1 = fanno_property_ratios(m1, gamma)
    p_2, r_2, p0_2, t_2 = fanno_property_ratios(m2, gamma)
    fig.add_trace(go.Scatter(x=[m1, m2], y=[t_1, t_2], mode='markers', marker=dict(color='red', size=8)), row=1, col=1)

    fig.update_layout(height=650, template="plotly_dark", showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

# ------------------------------------------
# ROUTINE 2: RAYLEIGH FLOW
# ------------------------------------------
elif selected_submodule == "GD02-R: Rayleigh Flow Analysis":
    st.title("Vayu Taral: Rayleigh Flow Solver (GD02-R)")
    
    with st.sidebar:
        st.header("MIMO Inputs")
        m1 = st.slider("Upstream Mach (M1)", 0.1, 3.0, 0.6)
        t1 = st.number_input("Static Temp (T1) [K]", value=300.0)
        p1 = st.number_input("Static Pressure (P1) [Pa]", value=101325.0)
        q_heat = st.number_input("Heat Added (Q) [J/kg]", value=50000.0)
        gamma = 1.4
        cp = 1004.5

    t01 = t1 * (1 + (gamma - 1) / 2 * m1**2)
    t02 = t01 + (q_heat / cp)
    t0_ratio1 = rayleigh_ratios(m1, gamma)[0]
    t0_star = t01 / t0_ratio1
    t0_ratio2 = t02 / t0_star

    if t0_ratio2 > 1.0:
        st.error(f"⚠️ THERMAL CHOKING: T02/T0* ({t0_ratio2:.3f}) > 1.0. Heat limit exceeded.")
        m2 = 1.0
    else:
        m2 = solve_m2_rayleigh(t0_ratio2, m1, gamma)

    fig = make_subplots(rows=2, cols=2, subplot_titles=("Total Temp (T0/T0*)", "Static Pressure (P/P*)", 
                                                        "Density (Rho/Rho*)", "Total Pressure Loss (P0/P0*)"))
    m_range = np.linspace(0.01, 3.5, 500)
    t0, p, rho, p0 = rayleigh_ratios(m_range, gamma)

    fig.add_trace(go.Scatter(x=m_range, y=t0, name="T0/T0*"), row=1, col=1)
    fig.add_trace(go.Scatter(x=m_range, y=p, name="P/P*"), row=1, col=2)
    fig.add_trace(go.Scatter(x=m_range, y=rho, name="Rho/Rho*"), row=2, col=1)
    fig.add_trace(go.Scatter(x=m_range, y=p0, name="P0/P0*"), row=2, col=2)

    fig.update_layout(height=650, template="plotly_dark", showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

# ------------------------------------------
# ROUTINE 3: SUBSONIC NOZZLE
# ------------------------------------------
elif selected_submodule == "GD05-Sub: Subsonic Nozzle Flow":
    st.title("Vayu Taral: Isentropic Subsonic Nozzle Solver")
    
    with st.sidebar:
        st.header("Geometry & Pressures")
        p0 = st.number_input("Stagnation Pressure (p0) [Pa]", value=200000.0)
        pb = st.slider("Back Pressure (pB) [Pa]", 50000.0, 200000.0, 150000.0)
        a_inlet, a_throat, a_exit = 2.0, 1.0, 1.2
        gamma = 1.4

    pe_choke = p0 * 0.5283
    if pb > pe_choke:
        verdict = "NOT CHOKED (Subsonic Flow)"
        exit_p_ratio = pb / p0
        func_me = lambda M: (1 + (gamma - 1) / 2 * M**2)**(-gamma / (gamma - 1)) - exit_p_ratio
        me = fsolve(func_me, 0.5)[0]
        a_star = a_exit / area_mach_relation(me, gamma)
    else:
        verdict = "CHOKED (Mt = 1.0)"
        a_star = a_throat
        me = solve_mach_from_area(a_exit / a_star, gamma, regime='supersonic')

    x = np.linspace(0, 10, 100)
    areas = a_inlet - (a_inlet - a_throat) * np.sin(np.pi * x / 10)
    machs = [solve_mach_from_area(a / a_star, gamma, regime='subsonic') for a in areas]

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=x, y=areas, name="Area Profile A(x)", line=dict(color='gray', dash='dash')))
    fig.add_trace(go.Scatter(x=x, y=machs, name="Mach Number M(x)", yaxis="y2", line=dict(color='cyan', width=4)))
    fig.update_layout(template="plotly_dark", title=f"Analysis Verdict: {verdict}",
                      yaxis=dict(title="Area [m²]"), yaxis2=dict(title="Mach", overlaying="y", side="right"))
    st.plotly_chart(fig, use_container_width=True)

# ------------------------------------------
# ROUTINE 4: SUPERSONIC C-D NOZZLE
# ------------------------------------------
elif selected_submodule == "GD05-Sup: Supersonic C-D Nozzle Flow":
    st.title("Vayu Taral: Supersonic C-D Nozzle Solver")
    
    with st.sidebar:
        st.header("Reservoir & Dimensions")
        p0 = st.number_input("Stagnation Pressure (p0) [Pa]", value=500000.0)
        pb = st.number_input("Back Pressure (pB) [Pa]", value=101325.0)
        at = st.number_input("Throat Area (At)", value=1.0)
        ae = st.number_input("Exit Area (Ae)", value=2.5)
        gamma = 1.4

    p_star = p0 * (2 / (gamma + 1))**(gamma / (gamma - 1))
    is_choked = pb / p0 <= p_star / p0
    a_star = at if is_choked else at * 1.1

    me_isen = solve_mach_from_area(ae / a_star, gamma, regime='supersonic')
    pe_isen = get_static_p(p0, me_isen, gamma)

    if pb > pe_isen * 1.2:
        regime = "Normal Shock in Divergent Section"
        color = "red"
    elif pb > pe_isen:
        regime = "Overexpanded (Oblique Shocks)"
        color = "orange"
    elif abs(pb - pe_isen) < 1000:
        regime = "Perfectly Expanded"
        color = "green"
    else:
        regime = "Underexpanded (Expansion Fans)"
        color = "cyan"

    st.subheader(f"Exhaust Status: :[{color}]{{{regime}}}")

    x = np.linspace(0, 10, 100)
    area_profile = np.where(x < 5, 2.0 - (2.0 - at) * (x / 5), at + (ae - at) * ((x - 5) / 5))
    mach_dist = [solve_mach_from_area(a / a_star, gamma, regime=('subsonic' if x[i] < 5 else 'supersonic')) for i, a in enumerate(area_profile)]
    p_dist = [get_static_p(p0, m, gamma) for m in mach_dist]

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=x, y=mach_dist, name="Mach Number", line=dict(color='cyan', width=3)))
    fig.add_trace(go.Scatter(x=x, y=p_dist, name="Static Pressure", yaxis="y2", line=dict(color='yellow', dash='dot')))
    fig.update_layout(template="plotly_dark", xaxis_title="Nozzle Station (x)",
                      yaxis=dict(title="Mach Number"), yaxis2=dict(title="Pressure (Pa)", overlaying="y", side="right"))
    st.plotly_chart(fig, use_container_width=True)