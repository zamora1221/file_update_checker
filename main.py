import streamlit as st
import pandas as pd
import os

UPLOAD_DIR = 'uploaded_files'
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Initialize session state to store previous uploads persistently
if 'comparison_results' not in st.session_state:
    st.session_state.comparison_results = {}

# Streamlit UI
st.title('Court Case Comparison Tool')

# Clear Session Button
if st.button('Clear Previous Session'):
    st.session_state.comparison_results = {}
    for file in os.listdir(UPLOAD_DIR):
        os.remove(os.path.join(UPLOAD_DIR, file))
    st.success('Previous session cleared successfully.')

# File uploaders and storing uploaded files
uploaded_file1 = st.file_uploader('Upload First Excel File', type=['xlsx'], key='file1')
if uploaded_file1:
    with open(os.path.join(UPLOAD_DIR, uploaded_file1.name), 'wb') as f:
        f.write(uploaded_file1.getbuffer())

uploaded_file2 = st.file_uploader('Upload Second Excel File', type=['xlsx'], key='file2')
if uploaded_file2:
    with open(os.path.join(UPLOAD_DIR, uploaded_file2.name), 'wb') as f:
        f.write(uploaded_file2.getbuffer())

# Get list of previously uploaded files
uploaded_files = os.listdir(UPLOAD_DIR)

# Dropdowns to select from previously uploaded files
selected_file1 = st.selectbox('Select First File', uploaded_files, index=0 if uploaded_files else None)
selected_file2 = st.selectbox('Select Second File', uploaded_files, index=1 if len(uploaded_files) > 1 else None)

# Read selected files
if selected_file1 and selected_file2:
    data1 = pd.read_excel(os.path.join(UPLOAD_DIR, selected_file1))
    data2 = pd.read_excel(os.path.join(UPLOAD_DIR, selected_file2))

    # Standardize columns
    data1.columns = ['name', 'dob', 'case_number', 'court_dates']
    data2.columns = ['name', 'dob', 'case_number', 'court_dates']

    # Ensure 'dob' is treated as text
    data1['dob'] = data1['dob'].astype(str)
    data2['dob'] = data2['dob'].astype(str)

    # Perform outer merge to identify differences
    comparison = data2.merge(
        data1,
        on=['name', 'dob', 'case_number'],
        how='outer',
        suffixes=('_new', '_old'),
        indicator=True
    )

    # Identify added, removed, and updated records
    added = comparison[comparison['_merge'] == 'left_only'][['name', 'dob', 'case_number', 'court_dates_new']]
    removed = comparison[comparison['_merge'] == 'right_only'][['name', 'dob', 'case_number', 'court_dates_old']]
    updated = comparison[(comparison['_merge'] == 'both') &
                         (comparison['court_dates_new'] != comparison['court_dates_old'])][
                             ['name', 'dob', 'case_number', 'court_dates_old', 'court_dates_new']
                         ]

    # Store results in session state
    st.session_state.comparison_results = {
        'added': added,
        'removed': removed,
        'updated': updated
    }

    # Display results persistently without download
    if not added.empty:
        st.subheader('Added Records')
        st.write(added)
    else:
        st.info('No new records added.')

    if not removed.empty:
        st.subheader('Removed Records')
        st.write(removed)
    else:
        st.info('No records removed.')

    if not updated.empty:
        st.subheader('Updated Records')
        st.write(updated)
    else:
        st.info('No records updated.')

    # Export Results Button
    if st.button('Export Results'):
        with pd.ExcelWriter(os.path.join(UPLOAD_DIR, 'comparison_results.xlsx')) as writer:
            added.to_excel(writer, sheet_name='Added', index=False)
            removed.to_excel(writer, sheet_name='Removed', index=False)
            updated.to_excel(writer, sheet_name='Updated', index=False)
        st.success('Results exported to uploaded_files/comparison_results.xlsx')

# Display previous results if session ends and reopens
if st.session_state.comparison_results:
    st.subheader('Previous Session Results')
    for key, df in st.session_state.comparison_results.items():
        if not df.empty:
            st.write(f'{key.capitalize()} Records')
            st.write(df)
