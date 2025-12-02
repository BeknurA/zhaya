
import streamlit as st
from ui import get_text

def show_digital_technologies_page(lang_choice):
    st.header(get_text("digital_technologies_title", lang_choice))

    st.markdown(get_text("digital_technologies_intro", lang_choice))

    st.subheader(get_text("digital_technologies_research_title", lang_choice))

    st.markdown("---")

    st.markdown(f"#### {get_text('digital_technologies_sensors_title', lang_choice)}")

    st.markdown(f"##### {get_text('digital_technologies_temp_sensors_title', lang_choice)}")
    st.markdown(f"""
    {get_text('digital_technologies_temp_sensors_purpose', lang_choice)}
    {get_text('digital_technologies_temp_sensors_examples', lang_choice)}
    {get_text('digital_technologies_temp_sensors_criteria', lang_choice)}
        - {get_text('digital_technologies_temp_sensors_cost', lang_choice)}
        - {get_text('digital_technologies_temp_sensors_accuracy', lang_choice)}
        - {get_text('digital_technologies_temp_sensors_applicability', lang_choice)}
    """)

    st.markdown(f"##### {get_text('digital_technologies_humidity_sensors_title', lang_choice)}")
    st.markdown(f"""
    {get_text('digital_technologies_humidity_sensors_purpose', lang_choice)}
    {get_text('digital_technologies_humidity_sensors_examples', lang_choice)}
    {get_text('digital_technologies_humidity_sensors_criteria', lang_choice)}
        - {get_text('digital_technologies_humidity_sensors_cost', lang_choice)}
        - {get_text('digital_technologies_humidity_sensors_accuracy', lang_choice)}
        - {get_text('digital_technologies_humidity_sensors_applicability', lang_choice)}
    """)

    st.markdown(f"##### {get_text('digital_technologies_ph_sensors_title', lang_choice)}")
    st.markdown(f"""
    {get_text('digital_technologies_ph_sensors_purpose', lang_choice)}
    {get_text('digital_technologies_ph_sensors_examples', lang_choice)}
    {get_text('digital_technologies_ph_sensors_criteria', lang_choice)}
        - {get_text('digital_technologies_ph_sensors_cost', lang_choice)}
        - {get_text('digital_technologies_ph_sensors_accuracy', lang_choice)}
        - {get_text('digital_technologies_ph_sensors_applicability', lang_choice)}
    """)

    st.markdown(f"##### {get_text('digital_technologies_aw_sensors_title', lang_choice)}")
    st.markdown(f"""
    {get_text('digital_technologies_aw_sensors_purpose', lang_choice)}
    {get_text('digital_technologies_aw_sensors_examples', lang_choice)}
    {get_text('digital_technologies_aw_sensors_criteria', lang_choice)}
        - {get_text('digital_technologies_aw_sensors_cost', lang_choice)}
        - {get_text('digital_technologies_aw_sensors_accuracy', lang_choice)}
        - {get_text('digital_technologies_aw_sensors_applicability', lang_choice)}
    """)

    st.markdown(f"##### {get_text('digital_technologies_bio_sensors_title', lang_choice)}")
    st.markdown(f"""
    {get_text('digital_technologies_bio_sensors_purpose', lang_choice)}
    {get_text('digital_technologies_bio_sensors_examples', lang_choice)}
    {get_text('digital_technologies_bio_sensors_criteria', lang_choice)}
        - {get_text('digital_technologies_bio_sensors_cost', lang_choice)}
        - {get_text('digital_technologies_bio_sensors_accuracy', lang_choice)}
        - {get_text('digital_technologies_bio_sensors_applicability', lang_choice)}
    """)

    st.markdown("---")

    st.markdown(f"#### {get_text('digital_technologies_iot_title', lang_choice)}")
    st.markdown(f"""
    {get_text('digital_technologies_iot_purpose', lang_choice)}
    {get_text('digital_technologies_iot_technologies', lang_choice)}
    {get_text('digital_technologies_iot_advantages', lang_choice)}
        - {get_text('digital_technologies_iot_monitoring', lang_choice)}
        - {get_text('digital_technologies_iot_forecasting', lang_choice)}
        - {get_text('digital_technologies_iot_automation', lang_choice)}
    {get_text('digital_technologies_iot_criteria', lang_choice)}
        - {get_text('digital_technologies_iot_cost', lang_choice)}
        - {get_text('digital_technologies_iot_scalability', lang_choice)}
        - {get_text('digital_technologies_iot_integration', lang_choice)}
    """)

    st.markdown("---")

    st.markdown(f"#### {get_text('digital_technologies_scada_title', lang_choice)}")
    st.markdown(f"""
    {get_text('digital_technologies_scada_purpose', lang_choice)}
    {get_text('digital_technologies_scada_difference', lang_choice)}
    {get_text('digital_technologies_scada_applicability', lang_choice)}
    {get_text('digital_technologies_scada_criteria', lang_choice)}
        - {get_text('digital_technologies_scada_reliability', lang_choice)}
        - {get_text('digital_technologies_scada_security', lang_choice)}
        - {get_text('digital_technologies_scada_visualization', lang_choice)}
    """)

    st.markdown("---")

    st.subheader(get_text("digital_technologies_relevant_tech_title", lang_choice))

    st.markdown(f"""
    {get_text('digital_technologies_relevant_tech_item1', lang_choice)}
    {get_text('digital_technologies_relevant_tech_item2', lang_choice)}
    {get_text('digital_technologies_relevant_tech_item3', lang_choice)}
    {get_text('digital_technologies_relevant_tech_item4', lang_choice)}
    """)

    st.subheader(get_text("digital_technologies_criteria_title", lang_choice))

    st.markdown(f"""
    {get_text('digital_technologies_criteria_cost', lang_choice)}
    {get_text('digital_technologies_criteria_accuracy', lang_choice)}
    {get_text('digital_technologies_criteria_applicability', lang_choice)}
    """)

    st.subheader(get_text("digital_technologies_report_title", lang_choice))

    st.success(f"""
    {get_text('digital_technologies_report_conclusion', lang_choice)}

    {get_text('digital_technologies_report_recommendation', lang_choice)}

    - {get_text('digital_technologies_report_stage1', lang_choice)}
    - {get_text('digital_technologies_report_stage2', lang_choice)}
    - {get_text('digital_technologies_report_stage3', lang_choice)}

    {get_text('digital_technologies_report_summary', lang_choice)}
    """)

    st.info(get_text("digital_technologies_report_disclaimer", lang_choice))
