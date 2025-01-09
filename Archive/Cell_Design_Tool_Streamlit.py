import altair as alt
import streamlit as st
import os
import pandas as pd
import csv
import numpy as np
from scipy import interpolate
from numpy import trapz
import matplotlib.pyplot as plt
from functools import reduce
import utils as ut
import time

time_start = time.time()

# Constants
HALF_CELL_DIR = os.getcwd() + '/cell_data/half_cell_voltage_curves'
CELL_DATA_DIR = os.getcwd() + '/cell_data'
CATHODE_OPTIONS = ['Faradion_Gen2_4.25V', 'Faradion_Gen2_4.35V', 'Faradion_Gen2_4.1V', 'Suxiang_XN33S',
                   'NFPP', 'Prussian White', 'NVP', 'NVPF', 'LFP', 'NMC622']
ANODE_OPTIONS = ['Faradion_HC', 'Faradion_HC_commercial',
                 'Kuraray_Kuranode (Type I)', 'Tin Powder_DGME', 'Synthetic Graphite', 'Anode Free', 'Pb Powder']

# Default Values
st.session_state.u_max_default = 4.2
st.session_state.u_min_default = 1.0
st.session_state.n_p_ratio_default = 1.13
st.session_state.target_capacity_default = 11934
st.session_state.start_capacity_default = 1215
st.session_state.anode_am1_default = 'Faradion_HC'
st.session_state.anode_am2_default = 'Faradion_HC_commercial'
st.session_state.anode_am3_default = 'Pb Powder'
st.session_state.anode_am1_irrev_scale_default = 1.0
st.session_state.anode_am1_rev_scale_default = 1.0
st.session_state.anode_am2_irrev_scale_default = 1.0
st.session_state.anode_am2_rev_scale_default = 1.0
st.session_state.anode_am3_irrev_scale_default = 1.0
st.session_state.anode_am3_rev_scale_default = 1.0
st.session_state.a_am1_default = 88.0
st.session_state.a_am2_default = 0.0
st.session_state.a_am3_default = 0.0
st.session_state.a_ac1_default = 0.0
st.session_state.a_ac2_default = 0.0
st.session_state.a_ca1_default = 9.0
st.session_state.a_ca2_default = 0.0
st.session_state.a_bd1_default = 3.0
st.session_state.a_bd2_default = 0.0
st.session_state.a_am1_density_default = 1.5
st.session_state.a_am2_density_default = 1.5
st.session_state.a_am3_density_default = 1.5
st.session_state.a_addcomp1_density_default = 2.0
st.session_state.a_addcomp2_density_default = 2.0
st.session_state.a_condaid1_density_default = 1.9
st.session_state.a_condaid2_density_default = 1.9
st.session_state.a_binder1_density_default = 1.7
st.session_state.a_binder2_density_default = 1.7
st.session_state.a_density_default = 0.85
st.session_state.cathode_am1_default = 'Faradion_Gen2_4.25V'
st.session_state.cathode_am2_default = 'Faradion_Gen2_4.35V'
st.session_state.cathode_am3_default = 'Faradion_Gen2_4.1V'
st.session_state.cathode_am1_irrev_scale_default = 1.0
st.session_state.cathode_am1_rev_scale_default = 1.0
st.session_state.cathode_am2_irrev_scale_default = 1.0
st.session_state.cathode_am2_rev_scale_default = 1.0
st.session_state.cathode_am3_irrev_scale_default = 1.0
st.session_state.cathode_am3_rev_scale_default = 1.0
st.session_state.c_am1_default = 89.0
st.session_state.c_am2_default = 0.0
st.session_state.c_am3_default = 0.0
st.session_state.c_ac1_default = 0.0
st.session_state.c_ac2_default = 0.0
st.session_state.c_ca1_default = 6.0
st.session_state.c_ca2_default = 0.0
st.session_state.c_bd1_default = 5.0
st.session_state.c_bd2_default = 0.0
st.session_state.c_am1_density_default = 4.0
st.session_state.c_am2_density_default = 4.0
st.session_state.c_am3_density_default = 4.0
st.session_state.c_addcomp1_density_default = 2.0
st.session_state.c_addcomp2_density_default = 2.0
st.session_state.c_condaid1_density_default = 1.9
st.session_state.c_condaid2_density_default = 1.9
st.session_state.c_binder1_density_default = 1.7
st.session_state.c_binder2_density_default = 1.7
st.session_state.c_density_default = 2.6
st.session_state.anode_ML_default = 5.25
st.session_state.cathode_ML_default = 10.68
st.session_state.cathode_stacks_default = 26
st.session_state.c_area_default = 172.83
st.session_state.cathode_uncoated_area_default = 8.22
st.session_state.cathode_cc_thickness_default = 15.0
st.session_state.cathode_cc_density_default = 2.7
st.session_state.anode_coated_area_default = 181.2
st.session_state.anode_uncoated_area_default = 7.55
st.session_state.anode_cc_thickness_default = 15
st.session_state.anode_cc_density_default = 2.7
st.session_state.separator_thickness_default = 16
st.session_state.separator_width_default = 100.0
st.session_state.separator_fold_length_default = 186
st.session_state.separator_density_default = 0.4
st.session_state.separator_porosity_default = 47.0
st.session_state.elyte_overhead_default = 10.0
st.session_state.elyte_density_default = 1.2
st.session_state.c_swell_factor_default = 1.0
st.session_state.a_swell_factor_default = 1.0
st.session_state.mylar_thickness_default = 113.0
st.session_state.mylar_areal_mass_default = 18.0
st.session_state.pos_terminal_mass_default = 1.0
st.session_state.neg_terminal_mass_default = 1.0
st.session_state.other_mass_default = 0.3
st.session_state.seal_1_length_default = 22.0
st.session_state.seal_2_length_default = 7.0
st.session_state.seal_3_length_default = 7.0
st.session_state.seal_4_length_default = 0.0
st.session_state.pouch_length_default = 188.0
st.session_state.pouch_width_default = 102.5
st.session_state.a_am1_cost_default = 14.27
st.session_state.a_am2_cost_default = 0
st.session_state.a_am3_cost_default = 0
st.session_state.a_addcomp1_cost_default = 0
st.session_state.a_addcomp2_cost_default = 0
st.session_state.a_condaid1_cost_default = 9
st.session_state.a_condaid2_cost_default = 9
st.session_state.a_binder1_cost_default = 10
st.session_state.a_binder2_cost_default = 10
st.session_state.c_am1_cost_default = 11.26
st.session_state.c_am2_cost_default = 0
st.session_state.c_am3_cost_default = 0
st.session_state.c_addcomp1_cost_default = 0
st.session_state.c_addcomp2_cost_default = 0
st.session_state.c_condaid1_cost_default = 9
st.session_state.c_condaid2_cost_default = 9
st.session_state.c_binder1_cost_default = 15
st.session_state.c_binder2_cost_default = 15
st.session_state.cathode_cc_cost_default = 6.3
st.session_state.anode_cc_cost_default = 6.3
st.session_state.separator_cost_default = 0.2
st.session_state.elyte_cost_default = 8.94
st.session_state.mylar_cost_default = 4.64
st.session_state.pos_terminal_cost_default = 16
st.session_state.neg_terminal_cost_default = 16

# State Management
st.session_state.open_circuit_voltages = {
    0: 0.0,
    10: 0.0,
    20: 0.0,
    30: 0.0,
    40: 0.0,
    50: 0.0,
    60: 0.0,
    70: 0.0,
    80: 0.0,
    90: 0.0,
    100: 0.0,
}
st.session_state.cell_details_energy = 0
st.session_state.cell_details_mass = 0
st.session_state.cell_details_thickness = 0
st.session_state.cell_details_specific_energy = 0
st.session_state.cell_details_cost = 0
st.session_state.cell_details_normalized_cost = 0
st.session_state.cell_details_energy_density = 0
st.session_state.voltage_curve_vals = {
    'positive_voltage_vals': [],
    'positive_capacity_vals': [],
    'negative_voltage_vals': [],
    'negative_capacity_vals': [],
    'full_voltage_vals1': [],
    'full_capacity_vals1': [],
    'full_voltage_vals2': [],
    'full_capacity_vals2': [],
}


###################################################################
#######             Render Introduction                   #########
###################################################################
st.set_page_config(layout="wide")
st.image('res/stanford_steer_logo.png', width=400)
st.title("Cell Design Tool")

###################################################################
#######                    Imports                        #########
###################################################################


def import_params(filepath):
    try:
        load_cell_params = pd.read_csv(filepath)
        params_list = load_cell_params['Value'].tolist()
        st.session_state.u_max = float(params_list[0])
        st.session_state.u_min = float(params_list[1])
        st.session_state.n_p_ratio = float(params_list[2])
        st.session_state.target_capacity = int(params_list[3])
        st.session_state.start_capacity = int(params_list[4])
        st.session_state.anode_am1 = params_list[5]
        st.session_state.anode_am2 = params_list[6]
        st.session_state.anode_am3 = params_list[7]
        st.session_state.anode_am1_irrev_scale = float(params_list[8])
        st.session_state.anode_am1_rev_scale = float(params_list[9])
        st.session_state.anode_am2_irrev_scale = float(params_list[10])
        st.session_state.anode_am2_rev_scale = float(params_list[11])
        st.session_state.anode_am3_irrev_scale = float(params_list[12])
        st.session_state.anode_am3_rev_scale = float(params_list[13])
        st.session_state.a_am1 = float(params_list[14])
        st.session_state.a_am2 = float(params_list[15])
        st.session_state.a_am3 = float(params_list[16])
        st.session_state.a_ac1 = float(params_list[17])
        st.session_state.a_ac2 = float(params_list[18])
        st.session_state.a_ca1 = float(params_list[19])
        st.session_state.a_ca2 = float(params_list[20])
        st.session_state.a_bd1 = float(params_list[21])
        st.session_state.a_bd2 = float(params_list[22])
        st.session_state.a_am1_density = float(params_list[23])
        st.session_state.a_am2_density = float(params_list[24])
        st.session_state.a_am3_density = float(params_list[25])
        st.session_state.a_addcomp1_density = float(params_list[26])
        st.session_state.a_addcomp2_density = float(params_list[27])
        st.session_state.a_condaid1_density = float(params_list[28])
        st.session_state.a_condaid2_density = float(params_list[29])
        st.session_state.a_binder1_density = float(params_list[30])
        st.session_state.a_binder2_density = float(params_list[31])
        st.session_state.a_density = float(params_list[32])
        st.session_state.cathode_am1 = params_list[33]
        st.session_state.cathode_am2 = params_list[34]
        st.session_state.cathode_am3 = params_list[35]
        st.session_state.cathode_am1_irrev_scale = float(
            params_list[36])
        st.session_state.cathode_am1_rev_scale = float(params_list[37])
        st.session_state.cathode_am2_irrev_scale = float(
            params_list[38])
        st.session_state.cathode_am2_rev_scale = float(params_list[39])
        st.session_state.cathode_am3_irrev_scale = float(
            params_list[40])
        st.session_state.cathode_am3_rev_scale = float(params_list[41])
        st.session_state.c_am1 = float(params_list[42])
        st.session_state.c_am2 = float(params_list[43])
        st.session_state.c_am3 = float(params_list[44])
        st.session_state.c_ac1 = float(params_list[45])
        st.session_state.c_ac2 = float(params_list[46])
        st.session_state.c_ca1 = float(params_list[47])
        st.session_state.c_ca2 = float(params_list[48])
        st.session_state.c_bd1 = float(params_list[49])
        st.session_state.c_bd2 = float(params_list[50])
        st.session_state.c_am1_density = float(params_list[51])
        st.session_state.c_am2_density = float(params_list[52])
        st.session_state.c_am3_density = float(params_list[53])
        st.session_state.c_addcomp1_density = float(params_list[54])
        st.session_state.c_addcomp2_density = float(params_list[55])
        st.session_state.c_condaid1_density = float(params_list[56])
        st.session_state.c_condaid2_density = float(params_list[57])
        st.session_state.c_binder1_density = float(params_list[58])
        st.session_state.c_binder2_density = float(params_list[59])
        st.session_state.c_density = float(params_list[60])
        st.session_state.anode_ML = float(params_list[61])
        st.session_state.cathode_ML = float(params_list[62])
        st.session_state.cathode_stacks = int(params_list[63])
        st.session_state.c_area = float(params_list[64])
        st.session_state.cathode_uncoated_area = float(params_list[66])
        st.session_state.cathode_cc_thickness = float(params_list[67])
        st.session_state.cathode_cc_density = float(params_list[68])
        st.session_state.anode_coated_area = float(params_list[69])
        st.session_state.anode_uncoated_area = float(params_list[70])
        st.session_state.anode_cc_thickness = float(params_list[71])
        st.session_state.anode_cc_density = float(params_list[72])
        st.session_state.separator_thickness = float(params_list[73])
        st.session_state.separator_width = float(params_list[74])
        st.session_state.separator_fold_length = float(params_list[75])
        st.session_state.separator_density = float(params_list[76])
        st.session_state.separator_porosity = float(params_list[77])
        st.session_state.elyte_overhead = float(params_list[78])
        st.session_state.elyte_density = float(params_list[79])
        st.session_state.c_swell_factor = float(params_list[80])
        st.session_state.a_swell_factor = float(params_list[81])
        st.session_state.mylar_thickness = float(params_list[82])
        st.session_state.mylar_areal_mass = float(params_list[83])
        st.session_state.pos_terminal_mass = float(params_list[84])
        st.session_state.neg_terminal_mass = float(params_list[85])
        st.session_state.other_mass = float(params_list[86])
        st.session_state.seal_1_length = float(params_list[87])
        st.session_state.seal_2_length = float(params_list[88])
        st.session_state.seal_3_length = float(params_list[89])
        st.session_state.seal_4_length = float(params_list[90])
        st.session_state.pouch_length = float(params_list[91])
        st.session_state.pouch_width = float(params_list[92])
        st.session_state.open_circuit_voltages[0] = float(params_list[93])
        st.session_state.open_circuit_voltages[10] = float(params_list[94])
        st.session_state.open_circuit_voltages[20] = float(params_list[95])
        st.session_state.open_circuit_voltages[30] = float(params_list[96])
        st.session_state.open_circuit_voltages[40] = float(params_list[97])
        st.session_state.open_circuit_voltages[50] = float(params_list[98])
        st.session_state.open_circuit_voltages[60] = float(params_list[99])
        st.session_state.open_circuit_voltages[70] = float(params_list[100])
        st.session_state.open_circuit_voltages[80] = float(params_list[101])
        st.session_state.open_circuit_voltages[90] = float(params_list[102])
        st.session_state.open_circuit_voltages[100] = float(params_list[103])
        st.session_state.a_am1_cost = float(params_list[104])
        st.session_state.a_am2_cost = float(params_list[105])
        st.session_state.a_am3_cost = float(params_list[106])
        st.session_state.a_addcomp1_cost = float(params_list[107])
        st.session_state.a_addcomp2_cost = float(params_list[108])
        st.session_state.a_condaid1_cost = float(params_list[109])
        st.session_state.a_condaid2_cost = float(params_list[110])
        st.session_state.a_binder1_cost = float(params_list[111])
        st.session_state.a_binder2_cost = float(params_list[112])
        st.session_state.c_am1_cost = float(params_list[113])
        st.session_state.c_am2_cost = float(params_list[114])
        st.session_state.c_am3_cost = float(params_list[115])
        st.session_state.c_addcomp1_cost = float(params_list[116])
        st.session_state.c_addcomp2_cost = float(params_list[117])
        st.session_state.c_condaid1_cost = float(params_list[118])
        st.session_state.c_condaid2_cost = float(params_list[119])
        st.session_state.c_binder1_cost = float(params_list[120])
        st.session_state.c_binder2_cost = float(params_list[121])
        st.session_state.cathode_cc_cost = float(params_list[122])
        st.session_state.anode_cc_cost = float(params_list[123])
        st.session_state.separator_cost = float(params_list[124])
        st.session_state.elyte_cost = float(params_list[125])
        st.session_state.mylar_cost = float(params_list[126])
        st.session_state.pos_terminal_cost = float(params_list[127])
        st.session_state.neg_terminal_cost = float(params_list[128])
    except:
        st.error(
            'An error occured. Please make sure cell design parameters are properly configured.')


st.write("")
st.subheader("Import Cell Specifications")

cols = st.columns(spec=[1, 1, 1], vertical_alignment="top")
with cols[0]:
    st.write("**Start with a Pre-Existing Design**")
    st.write(
        "*If you have a pre-existing cell design, import it here to load in cell parameters.*")
    cell_design_params_file = st.file_uploader(
        "", type=["csv"], label_visibility="collapsed", key='cell_design_params_file')
    if cell_design_params_file is not None:
        import_params(cell_design_params_file)
        st.write("*Now that you've uploaded your cell design parameters, use the \"Specify Cell Design\" tab below to confirm the density and cost of each component.*")
    cell_design_template = open(f'{CELL_DATA_DIR}/FAR_BL.csv')
    st.download_button('Download Cell Design Template', cell_design_template,
                       "sample_cell_design.csv", "text/csv")
with cols[1]:
    st.write("**Upload Cathode Active Materials**")
    st.write(
        "*Upload cathode half cell curves to use your cathode material during cell design.*")
    cathode_half_cell_files = st.file_uploader(
        "", type=["csv"], label_visibility="collapsed", key='cathode_half_cell_file', accept_multiple_files=True)
    half_cell_curve_template = open(f'{HALF_CELL_DIR}/Cathode_LFP.csv')
    st.download_button('Download Cathode Half Cell Curve Template', half_cell_curve_template,
                       "sample_cathode_half_cell_curve.csv", "text/csv")
    for cathode_half_cell_file in cathode_half_cell_files:
        if cathode_half_cell_file is not None:
            save_path = f'{HALF_CELL_DIR}/Cathode_{cathode_half_cell_file.name}'
            with open(save_path, 'wb') as f:
                f.write(cathode_half_cell_file.getvalue())
            active_material_name = os.path.splitext(
                cathode_half_cell_file.name)[0]
            CATHODE_OPTIONS.append(active_material_name)
with cols[2]:
    st.write("**Upload Anode Active Materials**")
    st.write(
        "*Upload anode half cell curves to use your anode material during cell design.*")
    anode_half_cell_files = st.file_uploader(
        "Upload a half cell curve", type=["csv"], label_visibility="collapsed", key='anode_half_cell_file', accept_multiple_files=True)
    half_cell_curve_template = open(
        f'{HALF_CELL_DIR}/Anode_Pb Powder.csv')
    st.download_button('Download Anode Half Cell Curve Template', half_cell_curve_template,
                       "sample_anode_half_cell_curve.csv", "text/csv")
    for anode_half_cell_file in anode_half_cell_files:
        if anode_half_cell_file is not None:
            save_path = f'{HALF_CELL_DIR}/Anode_{anode_half_cell_file.name}'
            with open(save_path, 'wb') as f:
                f.write(anode_half_cell_file.getvalue())
            active_material_name = os.path.splitext(
                anode_half_cell_file.name)[0]
            ANODE_OPTIONS.append(active_material_name)


###################################################################
#######        Render "Cell Design"  Section              #########
###################################################################
st.write("")
st.write("")
st.subheader("Specify Cell Design")
main_cols = st.columns(spec=[3, 2], vertical_alignment="top")
with main_cols[0]:
    tabs = st.tabs(["Cell Details", "Cathode Formulation",
                    "Anode Formulation", "Electrode Details", "Other Design Inputs", "Matching Curve"])

    # Tab 1: Cell Level Details
    with tabs[0]:
        u_max = st.number_input("Upper Cutoff Voltage (V)",
                                value=st.session_state.u_max_default, step=0.1, key="u_max")
        u_min = st.number_input(
            "Min Voltage (V)", value=st.session_state.u_min_default, step=0.1, key="u_min")
        n_p_ratio = st.number_input(
            "N/P Ratio", value=st.session_state.n_p_ratio_default, step=0.01)
        target_capacity = st.slider('Reversible Capacity (mAh)', min_value=0,
                                    max_value=20000, value=st.session_state.target_capacity_default, step=50, key="target_capacity")
        start_capacity = st.slider('Irreversible Capacity Loss (mAh)',
                                   min_value=0, max_value=6000, value=st.session_state.start_capacity_default, step=1, key="start_capacity")

    # Tab 2: Cathode Formulation
    with tabs[1]:
        st.subheader("Materials")

        cols = st.columns(spec=[2, 1, 1, 1, 1, 1], vertical_alignment="center")
        with cols[0]:
            st.write("**Material**")
        with cols[1]:
            st.write("**Composition (%)**")
        with cols[2]:
            st.write("**Density (g/cc)**")
        with cols[3]:
            st.write("**Cost ($/kg)**")
        with cols[4]:
            st.write("**Irrev. Cap Scaling**")
        with cols[5]:
            st.write("**Rev. Cap Scaling**")

        # Active Material 1
        cols = st.columns(spec=[2, 1, 1, 1, 1, 1], vertical_alignment="center")
        with cols[0]:
            cathode_am1 = st.selectbox("Active Material 1", CATHODE_OPTIONS,
                                       index=0, key="cathode_am1", label_visibility="collapsed")
        with cols[1]:
            c_am1 = st.number_input(
                "%", value=st.session_state.c_am1_default, key="c_am1", label_visibility="collapsed")
        with cols[2]:
            c_am1_density = st.number_input(
                "Density (g/cc)", value=st.session_state.c_am1_density_default, key="c_am1_density", label_visibility="collapsed")
        with cols[3]:
            c_am1_cost = st.number_input(
                "Cost ($/kg)", value=st.session_state.c_am1_cost_default, key="c_am1_cost", label_visibility="collapsed")
        with cols[4]:
            cathode_am1_irrev_scale = st.slider(
                "Irrev. Cap Scaling", min_value=0.7, max_value=1.3, value=st.session_state.cathode_am1_irrev_scale_default, step=0.01, key="cathode_am1_irrev_scale", label_visibility="collapsed")
        with cols[5]:
            cathode_am1_rev_scale = st.slider(
                "Rev. Cap Scaling", min_value=0.7, max_value=1.3, value=st.session_state.cathode_am1_rev_scale_default, step=0.01, key="cathode_am1_rev_scale", label_visibility="collapsed")

        # Active Material 2
        cols = st.columns(spec=[2, 1, 1, 1, 1, 1], vertical_alignment="center")
        with cols[0]:
            cathode_am2 = st.selectbox("Active Material 2", CATHODE_OPTIONS,
                                       index=CATHODE_OPTIONS.index(st.session_state.cathode_am2_default), key="cathode_am2", label_visibility="collapsed")
        with cols[1]:
            c_am2 = st.number_input(
                "%", value=st.session_state.c_am2_default, key="c_am2", label_visibility="collapsed")
        with cols[2]:
            c_am2_density = st.number_input(
                "Density (g/cc)", value=st.session_state.c_am2_density_default, key="c_am2_density", label_visibility="collapsed")
        with cols[3]:
            c_am2_cost = st.number_input(
                "Cost ($/kg)", value=st.session_state.c_am2_cost_default, key="c_am2_cost", label_visibility="collapsed")
        with cols[4]:
            cathode_am2_irrev_scale = st.slider(
                "Irrev. Cap Scaling", min_value=0.7, max_value=1.3, value=st.session_state.cathode_am2_irrev_scale_default, step=0.01, key="cathode_am2_irrev_scale", label_visibility="collapsed")
        with cols[5]:
            cathode_am2_rev_scale = st.slider(
                "Rev. Cap Scaling", min_value=0.7, max_value=1.3, value=st.session_state.cathode_am2_rev_scale_default, step=0.01, key="cathode_am2_rev_scale", label_visibility="collapsed")

        # Active Material 3
        cols = st.columns(spec=[2, 1, 1, 1, 1, 1], vertical_alignment="center")
        with cols[0]:
            cathode_am3 = st.selectbox("Active Material 3", CATHODE_OPTIONS,
                                       index=CATHODE_OPTIONS.index(st.session_state.cathode_am3_default), key="cathode_am3", label_visibility="collapsed")
        with cols[1]:
            c_am3 = st.number_input(
                "%", value=st.session_state.c_am3_default, key="c_am3", label_visibility="collapsed")
        with cols[2]:
            c_am3_density = st.number_input(
                "Density (g/cc)", value=st.session_state.c_am3_density_default, key="c_am3_density", label_visibility="collapsed")
        with cols[3]:
            c_am3_cost = st.number_input(
                "Cost ($/kg)", value=st.session_state.c_am3_cost_default, key="c_am3_cost", label_visibility="collapsed")
        with cols[4]:
            cathode_am3_irrev_scale = st.slider(
                "Irrev. Cap Scaling", min_value=0.7, max_value=1.3, value=st.session_state.cathode_am3_irrev_scale_default, step=0.01, key="cathode_am3_irrev_scale", label_visibility="collapsed")
        with cols[5]:
            cathode_am3_rev_scale = st.slider(
                "Rev. Cap Scaling", min_value=0.7, max_value=1.3, value=st.session_state.cathode_am3_rev_scale_default, step=0.01, key="cathode_am3_rev_scale", label_visibility="collapsed")

        # Additional Comp 1
        cols = st.columns(spec=[2, 1, 1, 1, 1, 1], vertical_alignment="center")
        with cols[0]:
            st.markdown("**Additional Comp 1**")
        with cols[1]:
            c_ac1 = st.number_input(
                "%", value=st.session_state.c_ac1_default, key="c_ac1", label_visibility="collapsed")
        with cols[2]:
            c_addcomp1_density = st.number_input(
                "Density (g/cc)", value=st.session_state.c_addcomp1_density_default, key="c_addcomp1_density", label_visibility="collapsed")
        with cols[3]:
            c_addcomp1_cost = st.number_input(
                "Cost ($/kg)", value=st.session_state.c_addcomp1_cost_default, key="c_addcomp1_cost", label_visibility="collapsed")

        # Additional Comp 2
        cols = st.columns(spec=[2, 1, 1, 1, 1, 1], vertical_alignment="center")
        with cols[0]:
            st.markdown("**Additional Comp 2**")
        with cols[1]:
            c_ac2 = st.number_input(
                "%", value=st.session_state.c_ac2_default, key="c_ac2", label_visibility="collapsed")
        with cols[2]:
            c_addcomp2_density = st.number_input(
                "Density (g/cc)", value=st.session_state.c_addcomp2_density_default, key="c_addcomp2_density", label_visibility="collapsed")
        with cols[3]:
            c_addcomp2_cost = st.number_input(
                "Cost ($/kg)", value=st.session_state.c_addcomp2_cost_default, key="c_addcomp2_cost", label_visibility="collapsed")

        # Conductive Aid 1
        cols = st.columns(spec=[2, 1, 1, 1, 1, 1], vertical_alignment="center")
        with cols[0]:
            st.markdown("**Conductive Aid 1**")
        with cols[1]:
            c_ca1 = st.number_input(
                "%", value=st.session_state.c_ca1_default, key="c_ca1", label_visibility="collapsed")
        with cols[2]:
            c_condaid1_density = st.number_input(
                "Density (g/cc)", value=st.session_state.c_condaid1_density_default, key="c_condaid1_density", label_visibility="collapsed")
        with cols[3]:
            c_condaid1_cost = st.number_input(
                "Cost ($/kg)", value=st.session_state.c_condaid1_cost_default, key="c_condaid1_cost", label_visibility="collapsed")

        # Conductive Aid 2
        cols = st.columns(spec=[2, 1, 1, 1, 1, 1], vertical_alignment="center")
        with cols[0]:
            st.markdown("**Conductive Aid 2**")
        with cols[1]:
            c_ca2 = st.number_input(
                "%", value=st.session_state.c_ca2_default, key="c_ca2", label_visibility="collapsed")
        with cols[2]:
            c_condaid2_density = st.number_input(
                "Density (g/cc)", value=st.session_state.c_condaid2_density_default, key="c_condaid2_density", label_visibility="collapsed")
        with cols[3]:
            c_condaid2_cost = st.number_input(
                "Cost ($/kg)", value=st.session_state.c_condaid2_cost_default, key="c_condaid2_cost", label_visibility="collapsed")

        # Binder 1
        cols = st.columns(spec=[2, 1, 1, 1, 1, 1], vertical_alignment="center")
        with cols[0]:
            st.markdown("**Binder 1**")
        with cols[1]:
            c_bd1 = st.number_input(
                "%", value=st.session_state.c_bd1_default, key="c_bd1", label_visibility="collapsed")
        with cols[2]:
            c_binder1_density = st.number_input(
                "Density (g/cc)", value=st.session_state.c_binder1_density_default, key="c_binder1_density", label_visibility="collapsed")
        with cols[3]:
            c_binder1_cost = st.number_input(
                "Cost ($/kg)", value=st.session_state.c_binder1_cost_default, key="c_binder1_cost", label_visibility="collapsed")

        # Binder 2
        cols = st.columns(spec=[2, 1, 1, 1, 1, 1], vertical_alignment="center")
        with cols[0]:
            st.markdown("**Binder 2**")
        with cols[1]:
            c_bd2 = st.number_input(
                "%", value=st.session_state.c_bd2_default, key="c_bd2", label_visibility="collapsed")
        with cols[2]:
            c_binder2_density = st.number_input(
                "Density (g/cc)", value=st.session_state.c_binder2_density_default, key="c_binder2_density", label_visibility="collapsed")
        with cols[3]:
            c_binder2_cost = st.number_input(
                "Cost ($/kg)", value=st.session_state.c_binder2_cost_default, key="c_binder2_cost", label_visibility="collapsed")

        # Validate percentage total
        ut.validate_formulation(c_am1, c_am2, c_am3, c_ac1,
                                c_ac2, c_ca1, c_ca2, c_bd1, c_bd2)

        st.subheader("Properties")
        c_density = st.number_input(
            "**Calender Density (g/cc)**", value=st.session_state.c_density_default, key="c_density")
        cathode_porosity = ut.porosity_calculator(c_am1, c_am1_density, c_am2, c_am2_density, c_am3, c_am3_density,
                                                  c_ac1, c_addcomp1_density, c_ac2, c_addcomp2_density,
                                                  c_ca1, c_condaid1_density, c_ca2, c_condaid2_density,
                                                  c_bd1, c_binder1_density, c_bd2, c_binder2_density,
                                                  c_density
                                                  )
        st.write(
            f"**Cathode Porosity:**\n\n {round(cathode_porosity, 2)} %")

    # Tab 3: Anode Formulation
    with tabs[2]:
        st.subheader("Materials")

        cols = st.columns(spec=[2, 1, 1, 1, 1, 1], vertical_alignment="center")
        with cols[0]:
            st.write("**Material**")
        with cols[1]:
            st.write("**Composition (%)**")
        with cols[2]:
            st.write("**Density (g/cc)**")
        with cols[3]:
            st.write("**Cost ($/kg)**")
        with cols[4]:
            st.write("**Irrev. Cap Scaling**")
        with cols[5]:
            st.write("**Rev. Cap Scaling**")

        # Active Material 1
        cols = st.columns(spec=[2, 1, 1, 1, 1, 1], vertical_alignment="center")
        with cols[0]:
            anode_am1 = st.selectbox("Active Material 1", ANODE_OPTIONS,
                                     index=ANODE_OPTIONS.index(st.session_state.anode_am1_default), key="anode_am1", label_visibility="collapsed")
        with cols[1]:
            a_am1 = st.number_input(
                "%", value=st.session_state.a_am1_default, key="a_am1", label_visibility="collapsed")
        with cols[2]:
            a_am1_density = st.number_input(
                "Density (g/cc)", value=st.session_state.a_am1_density_default, key="a_am1_density", label_visibility="collapsed")
        with cols[3]:
            a_am1_cost = st.number_input(
                "Cost ($/kg)", value=st.session_state.a_am1_cost_default, key="a_am1_cost", label_visibility="collapsed")
        with cols[4]:
            anode_am1_irrev_scale = st.slider(
                "Irrev. Cap Scaling", min_value=0.7, max_value=1.3, value=st.session_state.anode_am1_irrev_scale_default, step=0.01, key="a_am1_irrev_scale", label_visibility="collapsed")
        with cols[5]:
            anode_am1_rev_scale = st.slider(
                "Rev. Cap Scaling", min_value=0.7, max_value=1.3, value=st.session_state.anode_am1_rev_scale_default, step=0.01, key="a_am1_rev_scale", label_visibility="collapsed")

        # Active Material 2
        cols = st.columns(spec=[2, 1, 1, 1, 1, 1], vertical_alignment="center")
        with cols[0]:
            anode_am2 = st.selectbox("Active Material 2", ANODE_OPTIONS,
                                     index=ANODE_OPTIONS.index(st.session_state.anode_am2_default), key="anode_am2", label_visibility="collapsed")
        with cols[1]:
            a_am2 = st.number_input(
                "%", value=st.session_state.a_am2_default, key="a_am2", label_visibility="collapsed")
        with cols[2]:
            a_am2_density = st.number_input(
                "Density (g/cc)", value=st.session_state.a_am2_density_default, key="a_am2_density", label_visibility="collapsed")
        with cols[3]:
            a_am2_cost = st.number_input(
                "Cost ($/kg)", value=st.session_state.a_am2_cost_default, key="a_am2_cost", label_visibility="collapsed")
        with cols[4]:
            anode_am2_irrev_scale = st.slider(
                "Irrev. Cap Scaling", min_value=0.7, max_value=1.3, value=st.session_state.anode_am2_irrev_scale_default, step=0.01, key="anode_am2_irrev_scale", label_visibility="collapsed")
        with cols[5]:
            anode_am2_rev_scale = st.slider(
                "Rev. Cap Scaling", min_value=0.7, max_value=1.3, value=st.session_state.anode_am2_rev_scale_default, step=0.01, key="anode_am2_rev_scale", label_visibility="collapsed")

        # Active Material 3
        cols = st.columns(spec=[2, 1, 1, 1, 1, 1], vertical_alignment="center")
        with cols[0]:
            anode_am3 = st.selectbox("Active Material 3", ANODE_OPTIONS,
                                     index=ANODE_OPTIONS.index(st.session_state.anode_am3_default), key="anode_am3", label_visibility="collapsed")
        with cols[1]:
            a_am3 = st.number_input(
                "%", value=st.session_state.a_am3_default, key="a_am3", label_visibility="collapsed")
        with cols[2]:
            a_am3_density = st.number_input(
                "Density (g/cc)", value=st.session_state.a_am3_density_default, key="a_am3_density", label_visibility="collapsed")
        with cols[3]:
            a_am3_cost = st.number_input(
                "Cost ($/kg)", value=st.session_state.a_am3_cost_default, key="a_am3_cost", label_visibility="collapsed")
        with cols[4]:
            anode_am3_irrev_scale = st.slider(
                "Irrev. Cap Scaling", min_value=0.7, max_value=1.3, value=st.session_state.anode_am3_irrev_scale_default, step=0.01, key="anode_am3_irrev_box", label_visibility="collapsed")
        with cols[5]:
            anode_am3_rev_scale = st.slider("Rev. Cap Scaling", min_value=0.7, max_value=1.3,
                                            value=st.session_state.anode_am3_rev_scale_default, step=0.01, key="anode_am3_rev_scale", label_visibility="collapsed")

        # Additional Comp 1
        cols = st.columns(spec=[2, 1, 1, 1, 1, 1], vertical_alignment="center")
        with cols[0]:
            st.markdown("**Additional Comp 1**")
        with cols[1]:
            a_ac1 = st.number_input(
                "%", value=st.session_state.a_ac1_default, key="a_ac1", label_visibility="collapsed")
        with cols[2]:
            a_addcomp1_density = st.number_input(
                "Density (g/cc)", value=st.session_state.a_addcomp1_density_default, key="a_addcomp1_density", label_visibility="collapsed")
        with cols[3]:
            a_addcomp1_cost = st.number_input(
                "Cost ($/kg)", value=st.session_state.a_addcomp1_cost_default, key="a_addcomp1_cost", label_visibility="collapsed")

        # Additional Comp 2
        cols = st.columns(spec=[2, 1, 1, 1, 1, 1], vertical_alignment="center")
        with cols[0]:
            st.markdown("**Additional Comp 2**")
        with cols[1]:
            a_ac2 = st.number_input(
                "%", value=st.session_state.a_ac2_default, key="a_ac2", label_visibility="collapsed")
        with cols[2]:
            a_addcomp2_density = st.number_input(
                "Density (g/cc)", value=st.session_state.a_addcomp2_density_default, key="a_addcomp2_density", label_visibility="collapsed")
        with cols[3]:
            a_addcomp2_cost = st.number_input(
                "Cost ($/kg)", value=st.session_state.a_addcomp2_cost_default, key="a_addcomp2_cost", label_visibility="collapsed")

        # Conductive Aid 1
        cols = st.columns(spec=[2, 1, 1, 1, 1, 1], vertical_alignment="center")
        with cols[0]:
            st.markdown("**Conductive Aid 1**")
        with cols[1]:
            a_ca1 = st.number_input(
                "%", value=st.session_state.a_ca1_default, key="a_ca1", label_visibility="collapsed")
        with cols[2]:
            a_condaid1_density = st.number_input(
                "Density (g/cc)", value=st.session_state.a_condaid1_density_default, key="a_condaid1_density", label_visibility="collapsed")
        with cols[3]:
            a_condaid1_cost = st.number_input(
                "Cost ($/kg)", value=st.session_state.a_condaid1_cost_default, key="a_condaid1_cost", label_visibility="collapsed")

        # Conductive Aid 2
        cols = st.columns(spec=[2, 1, 1, 1, 1, 1], vertical_alignment="center")
        with cols[0]:
            st.markdown("**Conductive Aid 2**")
        with cols[1]:
            a_ca2 = st.number_input(
                "%", value=st.session_state.a_ca2_default, key="a_ca2", label_visibility="collapsed")
        with cols[2]:
            a_condaid2_density = st.number_input(
                "Density (g/cc)", value=st.session_state.a_condaid2_density_default, key="a_condaid2_density", label_visibility="collapsed")
        with cols[3]:
            a_condaid2_cost = st.number_input(
                "Cost ($/kg)", value=st.session_state.a_condaid2_cost_default, key="a_condaid2_cost", label_visibility="collapsed")

        # Binder 1
        cols = st.columns(spec=[2, 1, 1, 1, 1, 1], vertical_alignment="center")
        with cols[0]:
            st.markdown("**Binder 1**")
        with cols[1]:
            a_bd1 = st.number_input(
                "%", value=st.session_state.a_bd1_default, key="a_bd1", label_visibility="collapsed")
        with cols[2]:
            a_binder1_density = st.number_input(
                "Density (g/cc)", value=st.session_state.a_binder1_density_default, key="a_binder1_density", label_visibility="collapsed")
        with cols[3]:
            a_binder1_cost = st.number_input(
                "Cost ($/kg)", value=st.session_state.a_binder1_cost_default, key="a_binder1_cost", label_visibility="collapsed")

        # Binder 2
        cols = st.columns(spec=[2, 1, 1, 1, 1, 1], vertical_alignment="center")
        with cols[0]:
            st.markdown("**Binder 2**")
        with cols[1]:
            a_bd2 = st.number_input(
                "%", value=st.session_state.a_bd2_default, key="a_bd2", label_visibility="collapsed")
        with cols[2]:
            a_binder2_density = st.number_input(
                "Density (g/cc)", value=st.session_state.a_binder2_density_default, key="a_binder2_density", label_visibility="collapsed")
        with cols[3]:
            a_binder2_cost = st.number_input(
                "Cost ($/kg)", value=st.session_state.a_binder2_cost_default, key="a_binder2_cost", label_visibility="collapsed")

        # Validate percentage total
        ut.validate_formulation(a_am1, a_am2, a_am3, a_ac1,
                                a_ac2, a_ca1, a_ca2, a_bd1, a_bd2)

        st.subheader("Properties")
        a_density = st.number_input(
            "**Calender Density (g/cc)**", value=st.session_state.a_density_default, key="a_density")
        # Anode porosity
        anode_porosity = ut.porosity_calculator(a_am1, a_am1_density, a_am2, a_am2_density, a_am3, a_am3_density,
                                                a_ac1, a_addcomp1_density, a_ac2, a_addcomp2_density,
                                                a_ca1, a_condaid1_density, a_ca2, a_condaid2_density,
                                                a_bd1, a_binder1_density, a_bd2, a_binder2_density,
                                                a_density
                                                )
        st.write(f"**Anode Porosity:**\n\n {round(anode_porosity, 2)} %")

    # Tab 4: Electrode Details
    with tabs[3]:
        cathode_ML = st.slider("Cathode Mass Loading (mg/cm²)",
                               min_value=1.0, max_value=38.0, value=st.session_state.cathode_ML_default, step=0.01, key="cathode_ML")
        anode_ML = st.slider("Anode Mass Loading (mg/cm²)",
                             min_value=0.0, max_value=35.0, value=st.session_state.anode_ML_default, step=0.01, key="anode_ML")
        cathode_stacks = st.slider(
            "Number of Cathode Stacks", min_value=1, max_value=110, value=st.session_state.cathode_stacks_default, step=1, key="cathode_stacks")
        c_area = st.number_input(
            "Cathode Single Sided Area(cm²)", value=st.session_state.c_area_default, min_value=0.1, step=1.0, key="c_area")
        electrode_details_cols = st.columns(4)
        with electrode_details_cols[0]:
            st.write(
                f"**Cathode SS Thickness:**\n\n {round(cathode_ML / c_density / 1000 * 10000, 1)} µm")
        with electrode_details_cols[1]:
            st.write(
                f"**Anode SS Thickness:**\n\n {round(anode_ML / a_density / 1000 * 10000, 1)} µm")
        with electrode_details_cols[2]:
            c_am1_grams = (c_am1/100) * cathode_ML * \
                c_area * 2 * cathode_stacks / 1000
            cathode_am1_curve = pd.read_csv(os.path.join(
                HALF_CELL_DIR, 'Cathode_{0}.csv'.format(cathode_am1)))
            cathode_am1_curve['Absolute Capacity (mAh)'] = cathode_am1_curve['Specific Capacity (mAh/g)']*c_am1_grams
            y_interpCatCap12 = np.arange(0.5, 5.0, 0.001)
            x_interpCatCap12 = np.interp(y_interpCatCap12, cathode_am1_curve.loc[cathode_am1_curve['Step_ID'] == 2]['Voltage (V)'][::-1],
                                         cathode_am1_curve.loc[cathode_am1_curve['Step_ID'] == 2]['Absolute Capacity (mAh)'][::-1] * cathode_am1_irrev_scale * cathode_am1_rev_scale)
            interpCatCap12 = pd.DataFrame(
                {'Capacity': x_interpCatCap12, 'Voltage': y_interpCatCap12})
            c_am2_grams = (c_am2/100) * cathode_ML * \
                c_area * 2 * cathode_stacks / 1000
            cathode_am2_curve = pd.read_csv(os.path.join(
                HALF_CELL_DIR, 'Cathode_{0}.csv'.format(cathode_am2)))
            cathode_am2_curve['Absolute Capacity (mAh)'] = cathode_am2_curve['Specific Capacity (mAh/g)']*c_am2_grams
            y_interpCatCap22 = np.arange(0.5, 5.0, 0.001)
            x_interpCatCap22 = np.interp(y_interpCatCap22, cathode_am2_curve.loc[cathode_am2_curve['Step_ID'] == 2]['Voltage (V)'][::-1],
                                         cathode_am2_curve.loc[cathode_am2_curve['Step_ID'] == 2]['Absolute Capacity (mAh)'][::-1] * cathode_am2_irrev_scale * cathode_am2_rev_scale)
            interpCatCap22 = pd.DataFrame(
                {'Capacity': x_interpCatCap22, 'Voltage': y_interpCatCap22})
            c_am3_grams = (c_am3/100) * cathode_ML * \
                c_area * 2 * cathode_stacks / 1000
            cathode_am3_curve = pd.read_csv(os.path.join(
                HALF_CELL_DIR, 'Cathode_{0}.csv'.format(cathode_am3)))
            cathode_am3_curve['Absolute Capacity (mAh)'] = cathode_am3_curve['Specific Capacity (mAh/g)']*c_am3_grams
            y_interpCatCap32 = np.arange(0.5, 5.0, 0.001)
            x_interpCatCap32 = np.interp(y_interpCatCap32, cathode_am3_curve.loc[cathode_am3_curve['Step_ID'] == 2]['Voltage (V)'][::-1],
                                         cathode_am3_curve.loc[cathode_am3_curve['Step_ID'] == 2]['Absolute Capacity (mAh)'][::-1] * cathode_am3_irrev_scale * cathode_am3_rev_scale)
            interpCatCap32 = pd.DataFrame(
                {'Capacity': x_interpCatCap32, 'Voltage': y_interpCatCap32})
            cathodeX2Dfs = [interpCatCap12[::-1],
                            interpCatCap22[::-1], interpCatCap32[::-1]]
            mergedCathodeX2Df = reduce(lambda left, right: pd.merge(
                left, right, on='Voltage'), cathodeX2Dfs)
            mergedCathodeX2Df['Combined'] = (
                mergedCathodeX2Df.Capacity_x + mergedCathodeX2Df.Capacity_y + mergedCathodeX2Df.Capacity)
            reversible_cathode_cap = mergedCathodeX2Df['Combined'].iloc[-1]
            active_geo_area = c_area * 2 * cathode_stacks
            cathode_areal_cap = reversible_cathode_cap / active_geo_area
            st.write(
                f"**Cathode Areal Capacity:**\n\n {round(cathode_areal_cap, 2)} mAh/cm²")
        with electrode_details_cols[3]:
            active_geo_area = c_area * 2 * cathode_stacks
            effective_areal_cap = target_capacity / active_geo_area
            st.write(
                f"**Effective Areal Capacity:**\n\n {round(effective_areal_cap, 2)} mAh/cm²")

    # Tab 5: Other Design Inputs
    with tabs[4]:
        st.write("**Cathode Details**")
        cols = st.columns(6)
        with cols[0]:
            st.number_input(
                "Coated Area (cm²)", value=c_area, key="cathode_coated_area", disabled=True)
        with cols[1]:
            cathode_uncoated_area = st.number_input(
                "Bare Tab Area (cm²)", value=st.session_state.cathode_uncoated_area_default, key="cathode_uncoated_area")
        with cols[2]:
            cathode_cc_thickness = st.number_input(
                "CC Thickness (µm)", value=st.session_state.cathode_cc_thickness_default, key="cathode_cc_thickness")
        with cols[3]:
            cathode_cc_density = st.number_input(
                "CC Density (g/cc)", value=st.session_state.cathode_cc_density_default, key="cathode_cc_density")
        with cols[4]:
            cathode_cc_cost = st.number_input(
                "CC Cost ($/kg)", value=st.session_state.cathode_cc_cost_default, key="cathode_cc_cost")
        with cols[5]:
            cathode_ss_thickness = cathode_ML / \
                c_density / 1000 * 10000  # units in µm
            cathode_ds_thickness_value = cathode_ss_thickness * \
                2 + cathode_cc_thickness
            st.write(
                f"**DS Thickness:**\n\n {round(cathode_ds_thickness_value, 1)} µm")

        st.write("**Anode Details**")
        cols = st.columns(6)
        with cols[0]:
            anode_coated_area = st.number_input(
                "Coated Area (cm²)", value=st.session_state.anode_coated_area_default, key="anode_coated_area")
        with cols[1]:
            anode_uncoated_area = st.number_input(
                "Bare Tab Area (cm²)", value=st.session_state.anode_uncoated_area_default, key="anode_uncoated_area")
        with cols[2]:
            anode_cc_thickness = st.number_input(
                "CC Thickness (µm)", value=st.session_state.anode_cc_thickness_default, key="anode_cc_thickness")
        with cols[3]:
            anode_cc_density = st.number_input(
                "CC Density (g/cc)", value=st.session_state.anode_cc_density_default, key="anode_cc_density")
        with cols[4]:
            anode_cc_cost = st.number_input(
                "CC Cost ($/kg)", value=st.session_state.anode_cc_cost_default, key="anode_cc_cost")
        with cols[5]:
            anode_ss_thickness = anode_ML / \
                a_density / 1000 * 10000  # units in µm
            anode_ds_thickness_value = anode_ss_thickness*2 + anode_cc_thickness
            st.write(
                f"**DS Thickness:**\n\n {round(anode_ds_thickness_value, 1)} µm")

        st.write("**Separator Details**")
        cols = st.columns(3)
        with cols[0]:
            separator_thickness = st.number_input(
                "Thickness (µm)", value=st.session_state.separator_thickness_default, key="separator_thickness")
            separator_density = st.number_input(
                "Density (g/cc)", value=st.session_state.separator_density_default, key="separator_density")
        with cols[1]:
            separator_width = st.number_input(
                "Slit Width (mm)", value=st.session_state.separator_width_default, key="separator_width")
            separator_porosity = st.number_input(
                "Porosity (%)", value=st.session_state.separator_porosity_default, key="separator_porosity", min_value=0.0, max_value=100.0)
        with cols[2]:
            separator_fold_length = st.number_input(
                "Fold Length (mm)", value=st.session_state.separator_fold_length_default, key="separator_fold_length")
            separator_cost = st.number_input(
                "Cost ($/m²)", value=st.session_state.separator_cost_default, key="separator_cost")

        st.write("**Swelling Characteristics**")
        cols = st.columns(2)
        with cols[0]:
            c_swell_factor = st.number_input(
                "Cathode Swell Factor", value=st.session_state.c_swell_factor_default, key="c_swell_factor")
        with cols[1]:
            a_swell_factor = st.number_input(
                "Anode Swell Factor", value=st.session_state.a_swell_factor_default, key="a_swell_factor")

        st.write("**Electrolyte Details**")
        cols = st.columns(4)
        with cols[0]:
            elyte_density = st.number_input(
                "Density (g/cc)", value=st.session_state.elyte_density_default, key="elyte_density")
        with cols[1]:
            elyte_overhead = st.number_input(
                "Overfill (%)", value=st.session_state.elyte_overhead_default, key="elyte_overhead", min_value=0.0, max_value=100.0)
        with cols[2]:
            elyte_cost = st.number_input(
                "Cost ($/kg)", value=st.session_state.elyte_cost_default, key="elyte_cost")
        with cols[3]:
            cathode_ss_thickness = cathode_ML / \
                c_density / 1000 * 10000  # units in µm
            anode_ss_thickness = anode_ML / \
                a_density / 1000 * 10000  # units in µm
            total_cathode_pore_volume = (c_area * cathode_ss_thickness/10000 *
                                         c_swell_factor * 2 * cathode_stacks) * cathode_porosity/100
            total_anode_pore_volume = (anode_coated_area * anode_ss_thickness/10000 *
                                       a_swell_factor * 2 * (cathode_stacks+1)) * anode_porosity/100
            total_separator_pore_volume = (separator_thickness/10000 * (separator_width/10 *
                                                                        separator_fold_length/10)) * (cathode_stacks*2 + 3) * separator_porosity/100
            elyte_volume_in_pores = total_cathode_pore_volume + \
                total_anode_pore_volume + total_separator_pore_volume
            total_elyte_volume = elyte_volume_in_pores * (1+elyte_overhead/100)
            elyte_norm_amount = str(
                round(total_elyte_volume / (target_capacity/1000), 2))
            st.write(
                f"**Electrolyte Norm. Amount**\n\n {elyte_norm_amount} (mL/Ah)")

        st.write("**Inactive Material Details**")
        cols = st.columns(4)
        with cols[0]:
            mylar_thickness = st.number_input(
                "Laminate Thickness (µm)", value=st.session_state.mylar_thickness_default, key="mylar_thickness")
            pos_terminal_mass = st.number_input(
                "Positive Terminal Mass (g)", value=st.session_state.pos_terminal_mass_default, key="pos_terminal_mass")
            seal_1_length = st.number_input(
                "Seal 1 Length (mm)", value=st.session_state.seal_1_length_default, key="seal_1_length")
            pouch_length = st.number_input(
                "Pouch Length (mm)", value=st.session_state.pouch_length_default, key="pouch_length")
        with cols[1]:
            mylar_areal_mass = st.number_input(
                "Laminate Areal Mass (mg/cm²)", value=st.session_state.mylar_areal_mass_default, key="mylar_areal_mass")
            pos_terminal_cost = st.number_input(
                "Positive Terminal Cost ($/kg)", value=st.session_state.pos_terminal_cost_default, key="pos_terminal_cost")
            seal_2_length = st.number_input(
                "Seal 2 Length (mm)", value=st.session_state.seal_2_length_default, key="seal_2_length")
            pouch_width = st.number_input(
                "Pouch Width (mm)", value=st.session_state.pouch_width_default, key="pouch_width")
        with cols[2]:
            mylar_cost = st.number_input(
                "Laminate Cost ($/m²)", value=st.session_state.mylar_cost_default, key="mylar_cost")
            neg_terminal_mass = st.number_input(
                "Negative Terminal Mass (g)", value=st.session_state.neg_terminal_mass_default, key="neg_terminal_mass")
            seal_3_length = st.number_input(
                "Seal 3 Length (mm)", value=st.session_state.seal_3_length_default, key="seal_3_length")
        with cols[3]:
            other_mass = st.number_input(
                "Tape/Other Mass (g)", value=st.session_state.other_mass_default, key="other_mass")
            neg_terminal_cost = st.number_input(
                "Negative Terminal Cost ($/kg)", value=st.session_state.neg_terminal_cost_default, key="neg_terminal_cost")
            seal_4_length = st.number_input(
                "Seal 4 Length (mm)", value=st.session_state.seal_4_length_default, key="seal_4_length")

    # Tab 6: Matching Curve
    with tabs[5]:
        matching_curve_grams = st.slider('Matching Curve Mass (g)', min_value=0,
                                         max_value=1500, value=0, step=1)
        st.write("**Import a Matching Curve**")
        matching_curve_file = st.file_uploader(
            "Import a matching curve file to display a reference curve on the voltage plot.", type=["csv"], key='matching_curve_file')
        matching_curve_template = open(
            f'{CELL_DATA_DIR}/FAR_4V_experimental.csv')
        st.download_button('Download Matching Curve Template', matching_curve_template,
                           "sample_matching_curve.csv", "text/csv")

st.divider()

render_time = time.time()
os.write(
    1, f'Rendered "Specify Cell Design" in {render_time - time_start} seconds\n'.encode())


###################################################################
#######                    Render Plots                   #########
###################################################################
####### Perform Calculations ########
anode_porosity = ut.porosity_calculator(a_am1, a_am1_density, a_am2, a_am2_density, a_am3, a_am3_density,
                                        a_ac1, a_addcomp1_density, a_ac2, a_addcomp2_density,
                                        a_ca1, a_condaid1_density, a_ca2, a_condaid2_density,
                                        a_bd1, a_binder1_density, a_bd2, a_binder2_density,
                                        a_density
                                        )

cathode_porosity = ut.porosity_calculator(c_am1, c_am1_density, c_am2, c_am2_density, c_am3, c_am3_density,
                                          c_ac1, c_addcomp1_density, c_ac2, c_addcomp2_density,
                                          c_ca1, c_condaid1_density, c_ca2, c_condaid2_density,
                                          c_bd1, c_binder1_density, c_bd2, c_binder2_density,
                                          c_density
                                          )

anode_ss_thickness = anode_ML / a_density / 1000 * 10000  # units in µm
cathode_ss_thickness = cathode_ML / c_density / 1000 * 10000  # units in µm
active_geo_area = c_area * 2 * cathode_stacks

cathode_coat_mass_per_sheet = c_area * cathode_ML / 1000 * 2
cathode_foil_mass_per_sheet = (
    c_area + cathode_uncoated_area) * cathode_cc_thickness/10000 * cathode_cc_density
total_cathode_cc_cost = (
    cathode_foil_mass_per_sheet * cathode_stacks) / 1000 * cathode_cc_cost  # in $
total_cathode_mass = (cathode_coat_mass_per_sheet +
                      cathode_foil_mass_per_sheet) * cathode_stacks

anode_coat_mass_per_sheet = anode_coated_area * anode_ML / 1000 * 2
anode_foil_mass_per_sheet = (
    anode_coated_area + anode_uncoated_area) * anode_cc_thickness/10000 * anode_cc_density
total_anode_cc_cost = (anode_foil_mass_per_sheet *
                       (cathode_stacks+1)) / 1000 * anode_cc_cost  # in $
total_anode_mass = (anode_coat_mass_per_sheet +
                    anode_foil_mass_per_sheet) * (cathode_stacks+1)

total_separator_area = (
    separator_width/10 * separator_fold_length/10) * (cathode_stacks*2 + 3)  # cm2
total_separator_mass = (separator_thickness/10000 *
                        total_separator_area) * separator_density
total_separator_cost = total_separator_area/10000 * separator_cost  # in $

total_cathode_pore_volume = (c_area * cathode_ss_thickness/10000 *
                             c_swell_factor * 2 * cathode_stacks) * cathode_porosity/100
total_anode_pore_volume = (anode_coated_area * anode_ss_thickness /
                           10000 * a_swell_factor * 2 * (cathode_stacks+1)) * anode_porosity/100
total_separator_pore_volume = (separator_thickness/10000 * (separator_width/10 *
                                                            separator_fold_length/10)) * (cathode_stacks*2 + 3) * separator_porosity/100
elyte_volume_in_pores = total_cathode_pore_volume + \
    total_anode_pore_volume + total_separator_pore_volume

total_elyte_volume = elyte_volume_in_pores * (1+elyte_overhead/100)

total_elyte_mass = total_elyte_volume * elyte_density
total_elyte_cost = total_elyte_mass/1000 * elyte_cost  # in $

total_pouch_length = pouch_length + seal_1_length + seal_4_length
total_pouch_width = pouch_width + seal_2_length + seal_3_length
total_pouch_area = total_pouch_length/10 * total_pouch_width/10
total_pouch_cost = total_pouch_area/10000 * mylar_cost  # in $
total_pouch_mass = (2 * total_pouch_area * mylar_areal_mass)/1000

total_pos_term_cost = pos_terminal_mass/1000 * pos_terminal_cost  # in $
total_neg_term_cost = neg_terminal_mass/1000 * neg_terminal_cost  # in $

total_cell_mass = total_cathode_mass + total_anode_mass + total_separator_mass + \
    total_elyte_mass + total_pouch_mass + pos_terminal_mass + \
    neg_terminal_mass + other_mass  # in g
st.session_state.cell_details_mass = str(round(total_cell_mass, 2))

total_cathode_thickness = ((cathode_ss_thickness/1000 * c_swell_factor * 2) +
                           cathode_cc_thickness/1000) * cathode_stacks  # in mm
total_anode_thickness = ((anode_ss_thickness/1000 * a_swell_factor * 2) +
                         anode_cc_thickness/1000) * (cathode_stacks+1)  # in mm
total_separator_thickness = (
    separator_thickness * (cathode_stacks*2 + 3)) / 1000  # in mm
total_mylar_thickness = (mylar_thickness * 2)/1000

total_cell_thickness = total_cathode_thickness + total_anode_thickness + \
    total_separator_thickness + total_mylar_thickness
st.session_state.cell_details_thickness = str(
    round(total_cell_thickness, 2))
total_cell_volume = (total_cell_thickness/10 * (total_pouch_length) /
                     10 * (total_pouch_width)/10)/1000  # in Liters

############## Calculating Theoretical Cathode Half-Cell Curves ##############
c_am1_grams = (c_am1/100) * cathode_ML * c_area * 2 * cathode_stacks / 1000
c_am2_grams = (c_am2/100) * cathode_ML * c_area * 2 * cathode_stacks / 1000
c_am3_grams = (c_am3/100) * cathode_ML * c_area * 2 * cathode_stacks / 1000
c_addcomp1_grams = (c_ac1/100) * cathode_ML * \
    c_area * 2 * cathode_stacks / 1000
c_addcomp2_grams = (c_ac2/100) * cathode_ML * \
    c_area * 2 * cathode_stacks / 1000
c_condaid1_grams = (c_ca1/100) * cathode_ML * \
    c_area * 2 * cathode_stacks / 1000
c_condaid2_grams = (c_ca2/100) * cathode_ML * \
    c_area * 2 * cathode_stacks / 1000
c_binder1_grams = (c_bd1/100) * cathode_ML * \
    c_area * 2 * cathode_stacks / 1000
c_binder2_grams = (c_bd2/100) * cathode_ML * \
    c_area * 2 * cathode_stacks / 1000

total_c_am1_cost = c_am1_grams/1000 * c_am1_cost  # in $
total_c_am2_cost = c_am2_grams/1000 * c_am2_cost  # in $
total_c_am3_cost = c_am3_grams/1000 * c_am3_cost  # in $
total_c_addcomp1_cost = c_addcomp1_grams/1000 * c_addcomp1_cost  # in $
total_c_addcomp2_cost = c_addcomp2_grams/1000 * c_addcomp2_cost  # in $
total_c_condaid1_cost = c_condaid1_grams/1000 * c_condaid1_cost  # in $
total_c_condaid2_cost = c_condaid2_grams/1000 * c_condaid2_cost  # in $
total_c_binder1_cost = c_binder1_grams/1000 * c_binder1_cost  # in $
total_c_binder2_cost = c_binder2_grams/1000 * c_binder2_cost  # in $

# Cathode AM1 Capacity
cathode_am1_curve = pd.read_csv(os.path.join(
    HALF_CELL_DIR, 'Cathode_{0}.csv'.format(cathode_am1)))
cathode_am1_curve['Absolute Capacity (mAh)'] = cathode_am1_curve['Specific Capacity (mAh/g)']*c_am1_grams
# First charge -- Step 1
y_interpCatCap11 = np.arange(0.5, 5.0, 0.001)
x_interpCatCap11 = np.interp(y_interpCatCap11, cathode_am1_curve.loc[cathode_am1_curve['Step_ID'] == 1]['Voltage (V)'],
                             cathode_am1_curve.loc[cathode_am1_curve['Step_ID'] == 1]['Absolute Capacity (mAh)'] * cathode_am1_irrev_scale)
interpCatCap11 = pd.DataFrame(
    {'Capacity': x_interpCatCap11, 'Voltage': y_interpCatCap11})
# First discharge -- Step 2
y_interpCatCap12 = np.arange(0.5, 5.0, 0.001)
x_interpCatCap12 = np.interp(y_interpCatCap12, cathode_am1_curve.loc[cathode_am1_curve['Step_ID'] == 2]['Voltage (V)'][::-1],
                             cathode_am1_curve.loc[cathode_am1_curve['Step_ID'] == 2]['Absolute Capacity (mAh)'][::-1] * cathode_am1_irrev_scale * cathode_am1_rev_scale)
interpCatCap12 = pd.DataFrame(
    {'Capacity': x_interpCatCap12, 'Voltage': y_interpCatCap12})

# Cathode AM2 Capacity
cathode_am2_curve = pd.read_csv(os.path.join(
    HALF_CELL_DIR, 'Cathode_{0}.csv'.format(cathode_am2)))
cathode_am2_curve['Absolute Capacity (mAh)'] = cathode_am2_curve['Specific Capacity (mAh/g)']*c_am2_grams
# First charge -- Step 1
y_interpCatCap21 = np.arange(0.5, 5.0, 0.001)
x_interpCatCap21 = np.interp(y_interpCatCap21, cathode_am2_curve.loc[cathode_am2_curve['Step_ID'] == 1]['Voltage (V)'],
                             cathode_am2_curve.loc[cathode_am2_curve['Step_ID'] == 1]['Absolute Capacity (mAh)'] * cathode_am2_irrev_scale)
interpCatCap21 = pd.DataFrame(
    {'Capacity': x_interpCatCap21, 'Voltage': y_interpCatCap21})
# First discharge -- Step 2
y_interpCatCap22 = np.arange(0.5, 5.0, 0.001)
x_interpCatCap22 = np.interp(y_interpCatCap22, cathode_am2_curve.loc[cathode_am2_curve['Step_ID'] == 2]['Voltage (V)'][::-1],
                             cathode_am2_curve.loc[cathode_am2_curve['Step_ID'] == 2]['Absolute Capacity (mAh)'][::-1] * cathode_am2_irrev_scale * cathode_am2_rev_scale)
interpCatCap22 = pd.DataFrame(
    {'Capacity': x_interpCatCap22, 'Voltage': y_interpCatCap22})

# Cathode AM3 Capacity
cathode_am3_curve = pd.read_csv(os.path.join(
    HALF_CELL_DIR, 'Cathode_{0}.csv'.format(cathode_am3)))
cathode_am3_curve['Absolute Capacity (mAh)'] = cathode_am3_curve['Specific Capacity (mAh/g)']*c_am3_grams
# First charge -- Step 1
y_interpCatCap31 = np.arange(0.5, 5.0, 0.001)
x_interpCatCap31 = np.interp(y_interpCatCap31, cathode_am3_curve.loc[cathode_am3_curve['Step_ID'] == 1]['Voltage (V)'],
                             cathode_am3_curve.loc[cathode_am3_curve['Step_ID'] == 1]['Absolute Capacity (mAh)'] * cathode_am3_irrev_scale)
interpCatCap31 = pd.DataFrame(
    {'Capacity': x_interpCatCap31, 'Voltage': y_interpCatCap31})
# First discharge -- Step 2
y_interpCatCap32 = np.arange(0.5, 5.0, 0.001)
x_interpCatCap32 = np.interp(y_interpCatCap32, cathode_am3_curve.loc[cathode_am3_curve['Step_ID'] == 2]['Voltage (V)'][::-1],
                             cathode_am3_curve.loc[cathode_am3_curve['Step_ID'] == 2]['Absolute Capacity (mAh)'][::-1] * cathode_am3_irrev_scale * cathode_am3_rev_scale)
interpCatCap32 = pd.DataFrame(
    {'Capacity': x_interpCatCap32, 'Voltage': y_interpCatCap32})

cathodeX1Dfs = [interpCatCap11, interpCatCap21, interpCatCap31]
cathodeX2Dfs = [interpCatCap12[::-1],
                interpCatCap22[::-1], interpCatCap32[::-1]]

mergedCathodeX1Df = reduce(lambda left, right: pd.merge(
    left, right, on='Voltage'), cathodeX1Dfs)
mergedCathodeX2Df = reduce(lambda left, right: pd.merge(
    left, right, on='Voltage'), cathodeX2Dfs)

mergedCathodeX1Df['Combined'] = (
    mergedCathodeX1Df.Capacity_x + mergedCathodeX1Df.Capacity_y + mergedCathodeX1Df.Capacity)
mergedCathodeX2Df['Combined'] = (
    mergedCathodeX2Df.Capacity_x + mergedCathodeX2Df.Capacity_y + mergedCathodeX2Df.Capacity)

cathodeX1_lastValue = mergedCathodeX1Df['Combined'].iloc[-1]

mergedCathodeX2Df['Combined'] = mergedCathodeX2Df['Combined'] * - \
    1 + cathodeX1_lastValue
cathodeElectrode = pd.concat([mergedCathodeX1Df, mergedCathodeX2Df])

cathodeElectrodeCapacity = cathodeElectrode['Combined'].tolist()
cathodeElectrodeVoltage = cathodeElectrode['Voltage'].tolist()

############## Calculating Theoretical Anode Half-Cell Curve ##############
a_area = c_area

a_am1_grams = (a_am1/100) * anode_ML * a_area * 2 * cathode_stacks / 1000
a_am2_grams = (a_am2/100) * anode_ML * a_area * 2 * cathode_stacks / 1000
a_am3_grams = (a_am3/100) * anode_ML * a_area * 2 * cathode_stacks / 1000

a_addcomp1_grams = (a_ac1/100) * anode_ML * \
    a_area * 2 * cathode_stacks / 1000
a_addcomp2_grams = (a_ac2/100) * anode_ML * \
    a_area * 2 * cathode_stacks / 1000
a_condaid1_grams = (a_ca1/100) * anode_ML * \
    a_area * 2 * cathode_stacks / 1000
a_condaid2_grams = (a_ca2/100) * anode_ML * \
    a_area * 2 * cathode_stacks / 1000
a_binder1_grams = (a_bd1/100) * anode_ML * \
    a_area * 2 * cathode_stacks / 1000
a_binder2_grams = (a_bd2/100) * anode_ML * \
    a_area * 2 * cathode_stacks / 1000

total_a_am1_cost = a_am1_grams/1000 * a_am1_cost  # in $
total_a_am2_cost = a_am2_grams/1000 * a_am2_cost  # in $
total_a_am3_cost = a_am3_grams/1000 * a_am3_cost  # in $
total_a_addcomp1_cost = a_addcomp1_grams/1000 * a_addcomp1_cost  # in $
total_a_addcomp2_cost = a_addcomp2_grams/1000 * a_addcomp2_cost  # in $
total_a_condaid1_cost = a_condaid1_grams/1000 * a_condaid1_cost  # in $
total_a_condaid2_cost = a_condaid2_grams/1000 * a_condaid2_cost  # in $
total_a_binder1_cost = a_binder1_grams/1000 * a_binder1_cost  # in $
total_a_binder2_cost = a_binder2_grams/1000 * a_binder2_cost  # in $

# Anode AM1 Capacity
anode_am1_curve = pd.read_csv(os.path.join(
    HALF_CELL_DIR, 'Anode_{0}.csv'.format(anode_am1)))
anode_am1_curve['Absolute Capacity (mAh)'] = anode_am1_curve['Specific Capacity (mAh/g)']*a_am1_grams
# First charge -- Step 1
y_interpAndCap11 = np.arange(0, 2.0, 0.001)
x_interpAndCap11 = np.interp(y_interpAndCap11, anode_am1_curve.loc[anode_am1_curve['Step_ID'] == 1]['Voltage (V)'][::-1],
                             anode_am1_curve.loc[anode_am1_curve['Step_ID'] == 1]['Absolute Capacity (mAh)'][::-1] * anode_am1_irrev_scale)
interpAndCap11 = pd.DataFrame(
    {'Capacity': x_interpAndCap11, 'Voltage': y_interpAndCap11})
# First discharge -- Step 2
y_interpAndCap12 = np.arange(0, 2.0, 0.001)
x_interpAndCap12 = np.interp(y_interpAndCap12, anode_am1_curve.loc[anode_am1_curve['Step_ID'] == 2]['Voltage (V)'],
                             anode_am1_curve.loc[anode_am1_curve['Step_ID'] == 2]['Absolute Capacity (mAh)'] * anode_am1_irrev_scale * anode_am1_rev_scale)
interpAndCap12 = pd.DataFrame(
    {'Capacity': x_interpAndCap12, 'Voltage': y_interpAndCap12})

# Anode AM2 Capacity
anode_am2_curve = pd.read_csv(os.path.join(
    HALF_CELL_DIR, 'Anode_{0}.csv'.format(anode_am2)))
anode_am2_curve['Absolute Capacity (mAh)'] = anode_am2_curve['Specific Capacity (mAh/g)']*a_am2_grams
# First charge -- Step 1
y_interpAndCap21 = np.arange(0, 2.0, 0.001)
x_interpAndCap21 = np.interp(y_interpAndCap21, anode_am2_curve.loc[anode_am2_curve['Step_ID'] == 1]['Voltage (V)'][::-1],
                             anode_am2_curve.loc[anode_am2_curve['Step_ID'] == 1]['Absolute Capacity (mAh)'][::-1] * anode_am2_irrev_scale)
interpAndCap21 = pd.DataFrame(
    {'Capacity': x_interpAndCap21, 'Voltage': y_interpAndCap21})
# First discharge -- Step 2
y_interpAndCap22 = np.arange(0, 2.0, 0.001)
x_interpAndCap22 = np.interp(y_interpAndCap22, anode_am2_curve.loc[anode_am2_curve['Step_ID'] == 2]['Voltage (V)'],
                             anode_am2_curve.loc[anode_am2_curve['Step_ID'] == 2]['Absolute Capacity (mAh)'] * anode_am2_irrev_scale * anode_am2_rev_scale)
interpAndCap22 = pd.DataFrame(
    {'Capacity': x_interpAndCap22, 'Voltage': y_interpAndCap22})

# Anode AM3 Capacity
anode_am3_curve = pd.read_csv(os.path.join(
    HALF_CELL_DIR, 'Anode_{0}.csv'.format(anode_am3)))
anode_am3_curve['Absolute Capacity (mAh)'] = anode_am3_curve['Specific Capacity (mAh/g)']*a_am3_grams
# First charge -- Step 1
y_interpAndCap31 = np.arange(0, 2.0, 0.001)
x_interpAndCap31 = np.interp(y_interpAndCap31, anode_am3_curve.loc[anode_am3_curve['Step_ID'] == 1]['Voltage (V)'][::-1],
                             anode_am3_curve.loc[anode_am3_curve['Step_ID'] == 1]['Absolute Capacity (mAh)'][::-1] * anode_am3_irrev_scale)
interpAndCap31 = pd.DataFrame(
    {'Capacity': x_interpAndCap31, 'Voltage': y_interpAndCap31})
# First discharge -- Step 2
y_interpAndCap32 = np.arange(0, 2.0, 0.001)
x_interpAndCap32 = np.interp(y_interpAndCap32, anode_am3_curve.loc[anode_am3_curve['Step_ID'] == 2]['Voltage (V)'],
                             anode_am3_curve.loc[anode_am3_curve['Step_ID'] == 2]['Absolute Capacity (mAh)'] * anode_am3_irrev_scale * anode_am3_rev_scale)
interpAndCap32 = pd.DataFrame(
    {'Capacity': x_interpAndCap32, 'Voltage': y_interpAndCap32})

anodeX1Dfs = [interpAndCap11[::-1],
              interpAndCap21[::-1], interpAndCap31[::-1]]
anodeX2Dfs = [interpAndCap12, interpAndCap22, interpAndCap32]

mergedAnodeX1Df = reduce(lambda left, right: pd.merge(
    left, right, on='Voltage'), anodeX1Dfs)
mergedAnodeX2Df = reduce(lambda left, right: pd.merge(
    left, right, on='Voltage'), anodeX2Dfs)

mergedAnodeX1Df['Combined'] = (
    mergedAnodeX1Df.Capacity_x + mergedAnodeX1Df.Capacity_y + mergedAnodeX1Df.Capacity)
mergedAnodeX2Df['Combined'] = (
    mergedAnodeX2Df.Capacity_x + mergedAnodeX2Df.Capacity_y + mergedAnodeX2Df.Capacity)

anodeX1_lastValue = mergedAnodeX1Df['Combined'].iloc[-1]
mergedAnodeX2Df['Combined'] = mergedAnodeX2Df['Combined'] * - \
    1 + anodeX1_lastValue
anodeElectrode = pd.concat([mergedAnodeX1Df, mergedAnodeX2Df])

anodeElectrodeCapacity = anodeElectrode['Combined'].tolist()
anodeElectrodeVoltage = anodeElectrode['Voltage'].tolist()

total_cell_cost = sum([total_a_am1_cost, total_a_am2_cost, total_a_am3_cost,
                       total_a_addcomp1_cost, total_a_addcomp2_cost,
                       total_a_condaid1_cost, total_a_condaid2_cost,
                       total_a_binder1_cost, total_a_binder2_cost,
                       total_c_am1_cost, total_c_am2_cost, total_c_am3_cost,
                       total_c_addcomp1_cost, total_c_addcomp2_cost,
                       total_c_condaid1_cost, total_c_condaid2_cost,
                       total_c_binder1_cost, total_c_binder2_cost,
                       total_anode_cc_cost, total_cathode_cc_cost,
                       total_separator_cost, total_elyte_cost, total_pouch_cost,
                       total_pos_term_cost, total_neg_term_cost
                       ])

######## Calculate Theoretical Full Cell Curve ###########
finalAndNewx = np.arange(0, start_capacity + target_capacity)
finalAndNewy1 = np.interp(
    finalAndNewx, mergedAnodeX1Df['Combined'], mergedAnodeX1Df['Voltage'])
interpFinalAnd1 = pd.DataFrame(
    {'Capacity': finalAndNewx, 'Voltage': finalAndNewy1})

finalCatNewx = np.arange(0, start_capacity + target_capacity)
finalCatNewy1 = np.interp(
    finalCatNewx, mergedCathodeX1Df['Combined'], mergedCathodeX1Df['Voltage'])
interpFinalCat1 = pd.DataFrame(
    {'Capacity': finalCatNewx, 'Voltage': finalCatNewy1})

electrodesDf1 = [interpFinalCat1, interpFinalAnd1]

finalAndNewx = np.arange(start_capacity, start_capacity + target_capacity)
finalAndNewy2 = np.interp(
    finalAndNewx, mergedAnodeX2Df['Combined'].iloc[::-1], mergedAnodeX2Df['Voltage'].iloc[::-1])
interpFinalAnd2 = pd.DataFrame(
    {'Capacity': finalAndNewx, 'Voltage': finalAndNewy2})

finalCatNewx = np.arange(start_capacity, start_capacity + target_capacity)
finalCatNewy2 = np.interp(
    finalCatNewx, mergedCathodeX2Df['Combined'].iloc[::-1], mergedCathodeX2Df['Voltage'].iloc[::-1])
interpFinalCat2 = pd.DataFrame(
    {'Capacity': finalCatNewx, 'Voltage': finalCatNewy2})

electrodesDf2 = [interpFinalCat2, interpFinalAnd2]

fullCellDf1 = reduce(lambda left, right: pd.merge(
    left, right, on='Capacity'), electrodesDf1)
fullCellDf2 = reduce(lambda left, right: pd.merge(
    left, right, on='Capacity'), electrodesDf2)

fullCellDf1["Differenced"] = fullCellDf1.Voltage_x - fullCellDf1.Voltage_y
fullCellDf2["Differenced"] = fullCellDf2.Voltage_x - fullCellDf2.Voltage_y

cellCapacity1 = fullCellDf1['Capacity'].tolist()
cellVoltage1 = fullCellDf1['Differenced'].tolist()

cellCapacity2 = fullCellDf2['Capacity'].tolist()
cellVoltage2 = fullCellDf2['Differenced'].tolist()

############### Calculate Matching Curves ######################
if matching_curve_file:
    matching_curve_df = pd.read_csv(matching_curve_file)
    matching_curve_df['capacity'] = matching_curve_df['capacity'].apply(
        lambda x: x * matching_curve_grams)
    matching_curve_df['capacity'] = matching_curve_df['capacity']
    matching_curve_cap = matching_curve_df['capacity'].tolist()
    matching_curve_volt = matching_curve_df['voltage'].tolist()

############ Capture Session State Values ###################
max_capacity = max(cellCapacity2)
socVals = [x/max_capacity for x in cellCapacity2]
f = interpolate.interp1d(socVals, cellVoltage2, fill_value="extrapolate")
st.session_state.open_circuit_voltages[0] = str(u_min)
st.session_state.open_circuit_voltages[1] = str(f(0.1))
st.session_state.open_circuit_voltages[2] = str(f(0.2))
st.session_state.open_circuit_voltages[3] = str(f(0.3))
st.session_state.open_circuit_voltages[4] = str(f(0.4))
st.session_state.open_circuit_voltages[5] = str(f(0.5))
st.session_state.open_circuit_voltages[6] = str(f(0.6))
st.session_state.open_circuit_voltages[7] = str(f(0.7))
st.session_state.open_circuit_voltages[8] = str(f(0.8))
st.session_state.open_circuit_voltages[9] = str(f(0.9))
st.session_state.open_circuit_voltages[10] = str(u_max)
watt_hours = trapz(cellVoltage2, cellCapacity2)/1000
st.session_state.cell_details_energy = str(round(watt_hours, 2))
st.session_state.cell_details_specific_energy = str(
    round(watt_hours/(total_cell_mass/1000), 2))
st.session_state.cell_details_energy_density = str(
    round(watt_hours/total_cell_volume, 2))
st.session_state.cell_details_cost = str(round(total_cell_cost, 2))
st.session_state.cell_details_normalized_cost = str(
    round((total_cell_cost/(watt_hours/1000)), 1))
st.session_state.voltage_curve_vals['full_voltage_vals1'] = str(
    cellVoltage1)
st.session_state.voltage_curve_vals['full_capacity_vals1'] = str(
    cellCapacity1)
st.session_state.voltage_curve_vals['full_voltage_vals2'] = str(
    cellVoltage2)
st.session_state.voltage_curve_vals['full_capacity_vals2'] = str(
    cellCapacity2)
st.session_state.voltage_curve_vals['negative_voltage_vals'] = str(
    anodeElectrodeVoltage)
st.session_state.voltage_curve_vals['negative_capacity_vals'] = str(
    anodeElectrodeCapacity)
st.session_state.voltage_curve_vals['positive_voltage_vals'] = str(
    cathodeElectrodeVoltage)
st.session_state.voltage_curve_vals['positive_capacity_vals'] = str(
    cathodeElectrodeCapacity)

with main_cols[1]:
    ################## Plot Voltage Curve ###################
    # Define voltage curve data
    def sample_data(data):
        if (len(data) is 0):
            return data
        target_num_points = 400
        sample_rate = min(target_num_points/len(data), 1)
        return data[::int(1/sample_rate)]

    full_cell_voltage_ceiling = pd.DataFrame({
        'capacity': sample_data(cellCapacity1),
        'voltage': sample_data(cellVoltage1),
        'Type': ['Theoretical Full Cell Voltage' for _ in range(len(sample_data(cellCapacity1)))]
    })
    full_cell_voltage_floor = pd.DataFrame({
        'capacity': sample_data(cellCapacity2),
        'voltage': sample_data(cellVoltage2),
        'Type': ['Theoretical Full Cell Voltage Discharge' for _ in range(len(sample_data(cellCapacity2)))]
    })
    maxCathodeChargeValue = cathodeElectrodeCapacity.index(
        max(cathodeElectrodeCapacity))
    cathodeCapacityValuesCharge = cathodeElectrodeCapacity[:maxCathodeChargeValue]
    cathodeVoltageValuesCharge = cathodeElectrodeVoltage[:maxCathodeChargeValue]
    cathodeCapacityValuesDischarge = cathodeElectrodeCapacity[maxCathodeChargeValue:]
    cathodeVoltageValuesDischarge = cathodeElectrodeVoltage[maxCathodeChargeValue:]
    cathodeChargeCurve = pd.DataFrame({
        'capacity': sample_data(cathodeCapacityValuesCharge),
        'voltage': sample_data(cathodeVoltageValuesCharge),
        'Type': ['Cathode Voltage' for _ in range(len(sample_data(cathodeVoltageValuesCharge)))]
    })
    cathodeDischargeCurve = pd.DataFrame({
        'capacity': sample_data(cathodeCapacityValuesDischarge),
        'voltage': sample_data(cathodeVoltageValuesDischarge),
        'Type': ['Cathode Voltage Discharge' for _ in range(len(sample_data(cathodeVoltageValuesDischarge)))]
    })
    maxAnodeChargeValue = anodeElectrodeCapacity.index(
        max(anodeElectrodeCapacity))
    anodeCapacityValuesCharge = anodeElectrodeCapacity[:maxAnodeChargeValue]
    anodeVoltageValuesCharge = anodeElectrodeVoltage[:maxAnodeChargeValue]
    anodeCapacityValuesDischarge = anodeElectrodeCapacity[maxAnodeChargeValue:]
    anodeVoltageValuesDischarge = anodeElectrodeVoltage[maxAnodeChargeValue:]
    anodeChargeCurve = pd.DataFrame({
        'capacity': sample_data(anodeCapacityValuesCharge),
        'voltage': sample_data(anodeVoltageValuesCharge),
        'Type': ['Anode Voltage' for _ in range(len(sample_data(anodeCapacityValuesCharge)))]
    })
    anodeDischargeCurve = pd.DataFrame({
        'capacity': sample_data(anodeCapacityValuesDischarge),
        'voltage': sample_data(anodeVoltageValuesDischarge),
        'Type': ['Anode Voltage Discharge' for _ in range(len(sample_data(anodeCapacityValuesDischarge)))]
    })
    full_voltage_curve_data = [
        anodeChargeCurve, anodeDischargeCurve, cathodeChargeCurve, cathodeDischargeCurve, full_cell_voltage_ceiling, full_cell_voltage_floor]

    line_names = ['Anode Voltage', 'Anode Voltage Discharge', 'Cathode Voltage', 'Cathode Voltage Discharge',
                  'Theoretical Full Cell Voltage', 'Theoretical Full Cell Voltage Discharge']
    line_colors = ['red', 'red', 'blue', 'blue', 'black', 'black']
    legend_names = ['Anode Voltage', 'Cathode Voltage',
                    'Theoretical Full Cell Voltage']
    if matching_curve_file:
        print(matching_curve_cap)
        print(matching_curve_volt)
        maxMatchingChargeValue = matching_curve_volt.index(
            max(matching_curve_volt))
        matchingCapacityValuesCharge = matching_curve_cap[:maxMatchingChargeValue]
        matchingVoltageValuesCharge = matching_curve_volt[:maxMatchingChargeValue]
        matchingCapacityValuesDischarge = matching_curve_cap[maxMatchingChargeValue:]
        matchingVoltageValuesDischarge = matching_curve_volt[maxMatchingChargeValue:]
        print(matchingCapacityValuesCharge)
        print(matchingVoltageValuesCharge)
        print(matchingCapacityValuesDischarge)
        print(matchingVoltageValuesDischarge)
        matching_curve_charge = pd.DataFrame({
            'capacity': sample_data(matchingCapacityValuesCharge),
            'voltage': sample_data(matchingVoltageValuesCharge),
            'Type': ['Experimental Full Cell Voltage' for _entry in matchingCapacityValuesCharge]
        })
        matching_curve_discharge = pd.DataFrame({
            'capacity': sample_data(matchingCapacityValuesDischarge),
            'voltage': sample_data(matchingVoltageValuesDischarge),
            'Type': ['Experimental Full Cell Voltage Discharge' for _entry in matchingCapacityValuesDischarge]
        })
        full_voltage_curve_data.append(matching_curve_charge)
        full_voltage_curve_data.append(matching_curve_discharge)
        line_names.append('Experimental Full Cell Voltage')
        line_names.append('Experimental Full Cell Voltage Discharge')
        line_colors.append('orange')
        line_colors.append('orange')
        legend_names.append('Experimental Full Cell Voltage')

    full_voltage_curve_data = pd.concat(full_voltage_curve_data)

    # Define chart and lines
    base = alt.Chart(full_voltage_curve_data).properties(width=550, height=475)
    cell_voltage = base.mark_line().encode(
        x=alt.X('capacity', title='Capacity [mAh]', scale=alt.Scale(
            domain=[0, 25000])),  # Fixed x-axis from 0 to 25,000mAh
        y=alt.Y('voltage', title='Voltage [V]', scale=alt.Scale(
            domain=[0, max(4.5, .2+u_max)])),  # Fixed y-axis from 0 to 4.5V
        color=alt.Color('Type', scale=alt.Scale(
            domain=line_names, range=line_colors),
            legend=alt.Legend(values=legend_names)),
        size=alt.condition(
            alt.FieldOneOfPredicate(field='Type', oneOf=[
                                    'Theoretical Full Cell Voltage', 'Theoretical Full Cell Voltage Discharge']),
            alt.value(3),  # Thicker line for full cell voltage
            alt.value(1.25)   # Default thickness for other lines
        )
    ).interactive().properties(title=alt.TitleParams(text='Electrode Balancing & Theoretical Full Cell Voltage Derivation'))
    max_voltage_line = base.mark_rule().encode(
        y=alt.datum(u_max),
        size=alt.value(0.1),
        color=alt.value('#5885AF')
    )
    min_voltage_line = base.mark_rule().encode(
        y=alt.datum(u_min),
        size=alt.value(0.1),
        color=alt.value('#5885AF')
    )
    start_capacity_line = base.mark_rule().encode(
        x=alt.datum(start_capacity),
        size=alt.value(0.1),
        color=alt.value('#5885AF')
    )
    target_capacity_line = base.mark_rule().encode(
        x=alt.datum(start_capacity+target_capacity),
        size=alt.value(0.1),
        color=alt.value('#5885AF'),
    )
    second_target_capacity_line = base.mark_rule().encode(
        x=alt.datum((start_capacity+target_capacity)*n_p_ratio),
        size=alt.value(0.1),
        color=alt.value('#5885AF')
    )
    full_voltage_plot = cell_voltage+max_voltage_line+min_voltage_line + \
        start_capacity_line+target_capacity_line+second_target_capacity_line
    full_voltage_plot = full_voltage_plot.configure_legend(
        orient='bottom', title=None, labelFontSize=12, columns=2
    )
    st.altair_chart(full_voltage_plot, use_container_width=True)

    ####################### Plot BOM Breakdown ###########################
    pie_labels = ['CAM1', 'CAM2', 'CAM3', 'AAM1', 'AAM2', 'AAM3',
                  '+CBD', '-CBD', 'SEP', 'ELY', '+CC', '-CC', 'OTH']
    total_cell_cost = sum([total_a_am1_cost, total_a_am2_cost, total_a_am3_cost,
                           total_a_addcomp1_cost, total_a_addcomp2_cost,
                           total_a_condaid1_cost, total_a_condaid2_cost,
                           total_a_binder1_cost, total_a_binder2_cost,
                           total_c_am1_cost, total_c_am2_cost, total_c_am3_cost,
                           total_c_addcomp1_cost, total_c_addcomp2_cost,
                           total_c_condaid1_cost, total_c_condaid2_cost,
                           total_c_binder1_cost, total_c_binder2_cost,
                           total_anode_cc_cost, total_cathode_cc_cost,
                           total_separator_cost, total_elyte_cost, total_pouch_cost,
                           total_pos_term_cost, total_neg_term_cost
                           ])
    pie_costs = [total_c_am1_cost, total_c_am2_cost, total_c_am3_cost,
                 total_a_am1_cost, total_a_am2_cost, total_a_am3_cost,
                 sum([total_c_addcomp1_cost, total_c_addcomp2_cost, total_c_condaid1_cost,
                      total_c_condaid2_cost, total_c_binder1_cost, total_c_binder2_cost]),
                 sum([total_a_addcomp1_cost, total_a_addcomp2_cost, total_a_condaid1_cost,
                      total_a_condaid2_cost, total_a_binder1_cost, total_a_binder2_cost]),
                 total_separator_cost,
                 total_elyte_cost,
                 total_cathode_cc_cost, total_anode_cc_cost,
                 sum([total_pouch_cost, total_pos_term_cost, total_neg_term_cost])
                 ]
    pie_labels_cleaned = []
    pie_costs_cleaned = []
    i = 0
    for component in pie_costs:
        if component > 0:
            pie_costs_cleaned.append(component)
            pie_labels_cleaned.append(pie_labels[i])
        i += 1
    pie_cost_percentages = [
        cost / total_cell_cost for cost in pie_costs_cleaned]
    pie_chart_data = pd.DataFrame(
        {"category": pie_labels_cleaned, "value": pie_cost_percentages})

    # Create a categorical color scale with 13 unique colors
    color_scale = alt.Scale(
        domain=pie_labels_cleaned,
        range=['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
               '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf',
               '#aec7e8', '#ffbb78', '#98df8a']
    )
    base = alt.Chart(pie_chart_data).encode(
        alt.Theta("value:Q").stack(True),
        alt.Color("category:N", scale=color_scale, legend=alt.Legend(
            title="Component", orient="right", labelLimit=100))
    )
    pie = base.mark_arc(innerRadius=20, outerRadius=120, stroke="#fff")
    outer_label = base.mark_text(radius=140, size=12).encode(
        text=alt.Text("value:Q", format=".1%"),
    )
    inner_label = base.mark_text(radius=80, size=12, fontWeight="bold").encode(
        text=alt.condition(
            alt.datum.value > 0.1,
            "category:N",
            alt.value("")
        ),
        color=alt.value("white"),  # Force white color for inner labels
    )
    chart = alt.layer(pie, outer_label, inner_label).properties(
        title='Cell Cost Breakdown, Cost = ${}/kWh'.format(
            round((total_cell_cost/(watt_hours/1000)), 1))
    )
    st.altair_chart(chart, use_container_width=True)

render_plot_time = time.time()
os.write(
    1, f'Rendered "Charts" in {render_plot_time - render_time} seconds\n'.encode())


###################################################################
#######         Render Calculated Outputs Section         #########
###################################################################
st.subheader("Calculated Outputs")
cols = st.columns(7)
with cols[0]:
    st.write(
        f"**Cell Mass**\n\n {st.session_state.cell_details_mass}g")
    print(st.session_state.cell_details_mass)
with cols[1]:
    st.markdown(
        f"**Cell Thickness**\n\n {st.session_state.cell_details_thickness}mm")
with cols[2]:
    st.markdown(
        f"**Cell Cost**\n\n ${st.session_state.cell_details_cost}")
with cols[3]:
    st.markdown(
        f"**Cell Energy**\n\n {st.session_state.cell_details_energy} Wh")
with cols[4]:
    st.markdown(
        f"**Specific Energy**\n\n {st.session_state.cell_details_specific_energy} Wh/kg")
with cols[5]:
    st.markdown(
        f"**Specific Density**\n\n {st.session_state.cell_details_energy_density} Wh/L")
with cols[6]:
    st.markdown(
        f"**Normalized Cost**\n\n {st.session_state.cell_details_normalized_cost} $/kWh")
st.divider()

###################################################################
#######                  Exports Section                  #########
###################################################################


def generate_cell_design_csv():
    export_values_dict = {
        'u_max': u_max,
        'u_min': u_min,
        'n_p_ratio': n_p_ratio,
        'target_capacity': target_capacity,
        'start_capacity': start_capacity,
        'anode_am1': anode_am1,
        'anode_am2': anode_am2,
        'anode_am3': anode_am3,
        'anode_am1_irrev_scale': anode_am1_irrev_scale,
        'anode_am1_rev_scale': anode_am1_rev_scale,
        'anode_am2_irrev_scale': anode_am2_irrev_scale,
        'anode_am2_rev_scale': anode_am2_rev_scale,
        'anode_am3_irrev_scale': anode_am3_irrev_scale,
        'anode_am3_rev_scale': anode_am3_rev_scale,
        'a_am1': a_am1,
        'a_am2': a_am2,
        'a_am3': a_am3,
        'a_ac1': a_ac1,
        'a_ac2': a_ac2,
        'a_ca1': a_ca1,
        'a_ca2': a_ca2,
        'a_bd1': a_bd1,
        'a_bd2': a_bd2,
        'a_am1_density': a_am1_density,
        'a_am2_density': a_am2_density,
        'a_am3_density': a_am3_density,
        'a_addcomp1_density': a_addcomp1_density,
        'a_addcomp2_density': a_addcomp2_density,
        'a_condaid1_density': a_condaid1_density,
        'a_condaid2_density': a_condaid2_density,
        'a_binder1_density': a_binder1_density,
        'a_binder2_density': a_binder2_density,
        'a_density': a_density,
        'cathode_am1': cathode_am1,
        'cathode_am2': cathode_am2,
        'cathode_am3': cathode_am3,
        'cathode_am1_irrev_scale': cathode_am1_irrev_scale,
        'cathode_am1_rev_scale': cathode_am1_rev_scale,
        'cathode_am2_irrev_scale': cathode_am2_irrev_scale,
        'cathode_am2_rev_scale': cathode_am2_rev_scale,
        'cathode_am3_irrev_scale': cathode_am3_irrev_scale,
        'cathode_am3_rev_scale': cathode_am3_rev_scale,
        'c_am1': c_am1,
        'c_am2': c_am2,
        'c_am3': c_am3,
        'c_ac1': c_ac1,
        'c_ac2': c_ac2,
        'c_ca1': c_ca1,
        'c_ca2': c_ca2,
        'c_bd1': c_bd1,
        'c_bd2': c_bd2,
        'c_am1_density': c_am1_density,
        'c_am2_density': c_am2_density,
        'c_am3_density': c_am3_density,
        'c_addcomp1_density': c_addcomp1_density,
        'c_addcomp2_density': c_addcomp2_density,
        'c_condaid1_density': c_condaid1_density,
        'c_condaid2_density': c_condaid2_density,
        'c_binder1_density': c_binder1_density,
        'c_binder2_density': c_binder2_density,
        'c_density': c_density,
        'anode_ML': anode_ML,
        'cathode_ML': cathode_ML,
        'cathode_stacks': cathode_stacks,
        'c_area': c_area,
        'overhang': 0.0,
        'cathode_uncoated_area': cathode_uncoated_area,
        'cathode_cc_thickness': cathode_cc_thickness,
        'cathode_cc_density': cathode_cc_density,
        'anode_coated_area': anode_coated_area,
        'anode_uncoated_area': anode_uncoated_area,
        'anode_cc_thickness': anode_cc_thickness,
        'anode_cc_density': anode_cc_density,
        'separator_thickness': separator_thickness,
        'separator_width': separator_width,
        'separator_fold_length': separator_fold_length,
        'separator_density': separator_density,
        'separator_porosity': separator_porosity,
        'elyte_overhead': elyte_overhead,
        'elyte_density': elyte_density,
        'c_swell_factor': c_swell_factor,
        'a_swell_factor': a_swell_factor,
        'mylar_thickness': mylar_thickness,
        'mylar_areal_mass': mylar_areal_mass,
        'pos_terminal_mass': pos_terminal_mass,
        'neg_terminal_mass': neg_terminal_mass,
        'other_mass': other_mass,
        'seal_1_length': seal_1_length,
        'seal_2_length': seal_2_length,
        'seal_3_length': seal_3_length,
        'seal_4_length': seal_4_length,
        'pouch_length': pouch_length,
        'pouch_width': pouch_width,
        'soc_0': st.session_state.open_circuit_voltages[0],
        'soc_10': st.session_state.open_circuit_voltages[1],
        'soc_20': st.session_state.open_circuit_voltages[2],
        'soc_30': st.session_state.open_circuit_voltages[3],
        'soc_40': st.session_state.open_circuit_voltages[4],
        'soc_50': st.session_state.open_circuit_voltages[5],
        'soc_60': st.session_state.open_circuit_voltages[6],
        'soc_70': st.session_state.open_circuit_voltages[7],
        'soc_80': st.session_state.open_circuit_voltages[8],
        'soc_90': st.session_state.open_circuit_voltages[9],
        'soc_100': st.session_state.open_circuit_voltages[10],
        'a_am1_cost': a_am1_cost,
        'a_am2_cost': a_am2_cost,
        'a_am3_cost': a_am3_cost,
        'a_addcomp1_cost': a_addcomp1_cost,
        'a_addcomp2_cost': a_addcomp2_cost,
        'a_condaid1_cost': a_condaid1_cost,
        'a_condaid2_cost': a_condaid2_cost,
        'a_binder1_cost': a_binder1_cost,
        'a_binder2_cost': a_binder2_cost,
        'c_am1_cost': c_am1_cost,
        'c_am2_cost': c_am2_cost,
        'c_am3_cost': c_am3_cost,
        'c_addcomp1_cost': c_addcomp1_cost,
        'c_addcomp2_cost': c_addcomp2_cost,
        'c_condaid1_cost': c_condaid1_cost,
        'c_condaid2_cost': c_condaid2_cost,
        'c_binder1_cost': c_binder1_cost,
        'c_binder2_cost': c_binder2_cost,
        'cathode_cc_cost': cathode_cc_cost,
        'anode_cc_cost': anode_cc_cost,
        'separator_cost': separator_cost,
        'elyte_cost': elyte_cost,
        'mylar_cost': mylar_cost,
        'pos_terminal_cost': pos_terminal_cost,
        'neg_terminal_cost': neg_terminal_cost
    }
    df = pd.DataFrame(export_values_dict.items(),
                      columns=["Parameter", "Value"])
    return df.to_csv().encode('utf-8')


def generate_voltage_curve_csv():
    voltage_curve_dict = {'Full Cell Charge Voltage': eval(st.session_state.voltage_curve_vals['full_voltage_vals1']),
                          'Full Cell Charge Capacity': eval(st.session_state.voltage_curve_vals['full_capacity_vals1']),
                          'Full Cell Discharge Voltage': eval(st.session_state.voltage_curve_vals['full_voltage_vals2']),
                          'Full Cell Discharge Capacity': eval(st.session_state.voltage_curve_vals['full_capacity_vals2']),
                          'Positive Voltage': eval(st.session_state.voltage_curve_vals['positive_voltage_vals']),
                          'Positive Capacity': eval(st.session_state.voltage_curve_vals['positive_capacity_vals']),
                          'Negative Voltage': eval(st.session_state.voltage_curve_vals['negative_voltage_vals']),
                          'Negative Capacity': eval(st.session_state.voltage_curve_vals['negative_capacity_vals']),
                          }
    export_voltage_df = pd.DataFrame(
        dict([(k, pd.Series(v)) for k, v in voltage_curve_dict.items()]))
    return export_voltage_df.to_csv().encode('utf-8')


st.subheader("Export Cell Details")
cols = st.columns(2)
with cols[0]:
    st.write("**Export Cell Design Parameters**")
    st.write("*Enter a filename to export the cell design parameters as a csv.*")
    cell_design_filename = st.text_input(
        '', 'cell_design.csv', label_visibility='collapsed')
    cell_design_csv = generate_cell_design_csv()
    st.download_button('Export Cell Design', cell_design_csv,
                       cell_design_filename, "text/csv")
with cols[1]:
    st.write("**Export Cell Voltage Curve**")
    st.write("*Enter a filename to export the cell's voltage curve as a csv.*")
    voltage_curve_filename = st.text_input(
        '', 'voltage_curve.csv', label_visibility='collapsed')
    voltage_curve_csv = generate_voltage_curve_csv()
    st.download_button('Export Voltage Curve', voltage_curve_csv,
                       voltage_curve_filename, "text/csv")

time_end = time.time()
os.write(
    1, f'Rendered "Details" in {time_end - render_plot_time} seconds\n'.encode())
os.write(
    1, f'Loaded full webpage in {time_end - time_start} seconds\n'.encode())
os.write(1, b'Completed app load\n')
