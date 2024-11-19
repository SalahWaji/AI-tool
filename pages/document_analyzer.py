# pages/document_analyzer.py
import streamlit as st
from dotenv import load_dotenv
import openai
import os
import PyPDF2
import json
from io import BytesIO

def extract_text_from_pdf(file):
    pdf_reader = PyPDF2.PdfReader(file)
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text()
    return text

def get_personalized_summary(text, user_profile, custom_instructions=None):
    # Base system message
    system_message = f"""You are an intelligent document analyzer assistant. 
    User Profile:
    - Role: {user_profile['role']}
    - Interests: {', '.join(user_profile['interests'])}
    - Preferred Focus: {user_profile['focus']}
    - Summary Length: {user_profile['summary_length']}
    
    Additional Instructions: {custom_instructions if custom_instructions else 'None provided'}

    Based on this profile and any additional instructions, analyze the provided text.
    Focus on aspects most relevant to their role, interests, and specific requests.
    Format the response as:

    ### KEY POINTS:
    [Bullet points of main takeaways relevant to user's interests]

    ### DETAILED SUMMARY:
    [Detailed analysis based on user's preferred focus]

    ### RECOMMENDATIONS:
    [Action items or insights based on user's role]
    """

    if custom_instructions:
        system_message += f"\n\nPay special attention to user's specific request: {custom_instructions}"

    try:
        response = openai.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": f"Please analyze this text: {text}"}
            ],
            temperature=0.7
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error: {str(e)}"

def show_document_analyzer():
    st.title("📄 Smart Document Analyzer")
    st.markdown("""
    Get personalized document summaries based on your profile and needs.
    """)

    # User Profile Section
    with st.expander("📋 Configure Your Profile", expanded=True):
        st.header("Your Profile")
        
        # Load or initialize user profile
        if 'user_profile' not in st.session_state:
            st.session_state.user_profile = {
                'role': '',
                'interests': [],
                'focus': '',
                'summary_length': 'Medium'
            }

        col1, col2 = st.columns(2)
        
        with col1:
            role = st.selectbox(
                "What's your role?",
                ["Executive", "Manager", "Student", "Researcher", "Engineer", "Other"],
                key="role_select"
            )
            
            interests = st.multiselect(
                "What aspects interest you most?",
                ["Financial Metrics", "Technical Details", "Strategic Insights", 
                 "Market Trends", "Research Findings", "Performance Indicators",
                 "Risk Assessment", "Innovation", "Competitive Analysis"],
                key="interests_select"
            )

        with col2:
            focus = st.selectbox(
                "What's your preferred focus?",
                ["High-level Overview", "Detailed Analysis", "Technical Deep-dive", 
                 "Business Impact", "Academic Analysis"],
                key="focus_select"
            )
            
            summary_length = st.select_slider(
                "Preferred summary length",
                options=["Very Brief", "Brief", "Medium", "Detailed", "Very Detailed"],
                value="Medium",
                key="length_select"
            )

        if st.button("Save Profile", type="primary"):
            st.session_state.user_profile = {
                'role': role,
                'interests': interests,
                'focus': focus,
                'summary_length': summary_length
            }
            st.success("✅ Profile saved! Your summaries will be personalized based on these preferences.")

    # Document Analysis Section
    st.header("Document Analysis")
    
    # File Upload
    uploaded_file = st.file_uploader(
        "Upload your document", 
        type=['pdf', 'txt']
    )
    
    # Custom Instructions
    custom_instructions = st.text_area(
        "Additional Instructions (Optional)",
        placeholder="Add any specific requirements or questions about the document. For example:\n" +
                   "- Focus on the methodology section\n" +
                   "- Extract all numerical data\n" +
                   "- Compare with industry standards\n" +
                   "- Explain technical terms",
        help="Your custom instructions will guide the analysis focus"
    )

    if uploaded_file is not None:
        try:
            # Extract text based on file type
            if uploaded_file.type == "application/pdf":
                text = extract_text_from_pdf(uploaded_file)
                st.success("✅ PDF processed successfully!")
            else:
                text = uploaded_file.getvalue().decode('utf-8')
                st.success("✅ Text file processed successfully!")

            # Show processing message
            with st.spinner('🔄 Analyzing document...'):
                if st.session_state.user_profile['role']:
                    summary = get_personalized_summary(text, st.session_state.user_profile, custom_instructions)
                    
                    # Create tabs for different viewing options
                    tab1, tab2 = st.tabs(["📊 Formatted Analysis", "📝 Raw Text"])
                    
                    with tab1:
                        # Split and display sections with copy buttons for each
                        sections = summary.split('###')
                        for section in sections:
                            if section.strip():
                                title, content = section.strip().split('\n', 1)
                                col1, col2 = st.columns([0.9, 0.1])
                                with col1:
                                    st.subheader(title.strip())
                                with col2:
                                    if st.button("📋", key=f"copy_{title}", help="Copy this section"):
                                        st.session_state[f'copy_{title}'] = content.strip()
                                        st.success("Copied!")
                                st.markdown(content.strip())
                                st.divider()
                    
                    with tab2:
                        st.code(summary, language="markdown")
                        col1, col2 = st.columns([0.5, 0.5])
                        with col1:
                            if st.button("📋 Copy Full Analysis"):
                                st.code(summary)
                                st.success("Click the copy button in the code block above!")
                        with col2:
                            # Generate download button
                            if st.button("⬇️ Download Analysis"):
                                # Create download link
                                filename = "document_analysis.md"
                                st.download_button(
                                    label="Click to Download",
                                    data=summary,
                                    file_name=filename,
                                    mime="text/markdown"
                                )
                else:
                    st.warning("⚠️ Please save your profile first to get personalized analysis.")

        except Exception as e:
            st.error(f"Error processing file: {str(e)}")

    # Tips and Examples
    with st.expander("📚 Tips for Better Results"):
        st.markdown("""
        ### Profile Tips
        - Be specific with your role and interests
        - Choose a focus that matches your current needs
        - Adjust summary length based on your time constraints
        
        ### Custom Instructions Tips
        - Be specific about what you're looking for
        - Mention any particular sections of interest
        - Ask for specific formats or comparisons
        - Request explanations of complex terms
        
        ### Document Tips
        - Ensure PDFs are text-searchable
        - Text files should be in UTF-8 encoding
        
        ### Example Use Cases
        1. **Executives**: Focus on KPIs and strategic insights
        2. **Students**: Focus on key concepts and summaries
        3. **Researchers**: Focus on methodology and findings
        4. **Engineers**: Focus on technical specifications and requirements
        """)