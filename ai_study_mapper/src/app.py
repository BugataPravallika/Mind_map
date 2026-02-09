import streamlit as st
import os
import sys

# Add src to python path to find modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.pipeline import StudyMapPipeline

@st.cache_resource
def get_pipeline(offline_mode: bool, model_speed: str):
    model_name = "google/flan-t5-base" if model_speed == "High Quality" else "google/flan-t5-small"
    return StudyMapPipeline(prefer_offline=offline_mode, model_name=model_name)

def main():
    st.set_page_config(page_title="AI Study Map Generator", layout="wide")
    
    st.title("🧠 AI Study Map Generator")
    st.markdown("Convert your study materials into simple mind maps and plans.")
    
    # Sidebar for inputs
    st.sidebar.header("Configuration")
    uploaded_files = st.sidebar.file_uploader("Upload Documents (PDF, DOCX) or Video", accept_multiple_files=True)
    
    available_time = st.sidebar.slider("Daily Study Time (minutes)", 15, 240, 60)
    target_lang = st.sidebar.selectbox("Target Language", ["en", "fr", "es", "de", "it", "pt"])
    
    # Speed/Quality Toggle
    st.sidebar.markdown("### ⚡ Performance")
    model_speed = st.sidebar.select_slider(
        "AI Engine Speed",
        options=["Fast (Turbo)", "High Quality"],
        value="High Quality",
        help="Turbo uses a smaller model for instant results. High Quality is better for complex science/law."
    )
    
    generate_audio = st.sidebar.checkbox("Generate AI audio summary", value=False)
    offline_mode = st.sidebar.checkbox("Force Offline mode", value=False)
    
    # Cognitive Load Control
    st.sidebar.markdown("### 🧠 Cognitive Load")
    complexity = st.sidebar.select_slider(
        "Mind Map Detail",
        options=["Low", "Medium", "High"],
        value="Medium"
    )

    start_btn = st.sidebar.button("Generate Study Map")
    
    if start_btn and uploaded_files:
        with st.spinner("Preparing AI Engine..."):
            try:
                # Initialize Pipeline once (Cached)
                pipeline = get_pipeline(offline_mode, model_speed)
                
                # Save uploaded files temporarily
                input_dir = "data/input"
                if not os.path.exists(input_dir):
                    os.makedirs(input_dir)
                
                file_paths = []
                for up_file in uploaded_files:
                    path = os.path.join(input_dir, up_file.name)
                    with open(path, "wb") as f:
                        f.write(up_file.getbuffer())
                    file_paths.append(path)

                # Run Pipeline
                with st.spinner("Processing content..."):
                    results = pipeline.run(
                        file_paths=file_paths,
                        target_lang=target_lang,
                        available_time_mins=available_time,
                        generate_audio=generate_audio,
                        complexity=complexity,
                    )
                
                if results:
                    st.success("Processing Complete!")
                    
                    # Layout Results
                    col1, col2 = st.columns([2, 1])
                    
                    with col1:
                        st.subheader("📚 Revision Sheet")
                        if 'map_path' in results:
                            with open(results['map_path'], 'r', encoding='utf-8') as f:
                                html_data = f.read()
                            st.components.v1.html(html_data, height=900, scrolling=True)
                            
                            st.download_button(
                                label="Download Revision Sheet (HTML)",
                                data=html_data,
                                file_name="study_revision_sheet.html",
                                mime="text/html"
                            )
                            
                        st.subheader("Simplified Summary")
                        st.text_area("Summary", results.get("simplified_text", ""), height=300)

                        if results.get("topics"):
                            st.subheader("Topics (clustered)")
                            st.dataframe(
                                [
                                    {
                                        "topic": t.get("title"),
                                        "priority": t.get("priority"),
                                        "top_terms": ", ".join(t.get("top_terms") or []),
                                    }
                                    for t in results["topics"]
                                ],
                                use_container_width=True,
                            )
                        
                    with col2:
                        st.subheader("Study Plan")
                        plan = results.get("study_plan", {})
                        if plan:
                            st.info(f"Estimated Total Time: {plan.get('total_estimated_minutes')} mins")
                            if plan.get("daily_usable_minutes"):
                                st.caption(
                                    f"Daily plan uses ~{plan.get('daily_usable_minutes')} mins (keeps buffer for breaks)."
                                )
                            for day_info in plan.get("roadmap", []):
                                with st.expander(f"Day {day_info['day']}"):
                                    for topic in day_info['topics']:
                                        st.write(
                                            f"- **{topic['topic']}** ({topic['time_minutes']}m) — *{topic.get('priority','')}*"
                                        )
                                    if day_info.get("suggestion"):
                                        st.caption(day_info["suggestion"])
                        
                        st.subheader("Audio Summary")
                        if 'audio_path' in results and os.path.exists(results['audio_path']):
                            st.audio(results['audio_path'])
                        elif generate_audio:
                            st.caption("Audio was requested but could not be generated (model missing or offline issue).")

                        # Quiz is now embedded in the HTML Revision Sheet.
                        pass
                        
                        if target_lang != "en":
                            st.subheader(f"Translation ({target_lang})")
                            st.write(results.get("translated_text", ""))

                        if results.get("detected_language"):
                            st.subheader("Detected input language")
                            st.write(results["detected_language"])
                            
            except Exception as e:
                st.error(f"An error occurred: {e}")
                import traceback
                st.text(traceback.format_exc())
    
    elif start_btn and not uploaded_files:
        st.warning("Please upload at least one file.")

if __name__ == "__main__":
    main()
