"""
AI Chat Tab - Context-aware drug intelligence assistant
"""

import streamlit as st


def render(drug_name: str):
    """
    Render AI chat tab with context injection.

    Args:
        drug_name: Name of selected drug
    """

    st.subheader(f"AI Assistant - {drug_name}")

    st.markdown("""
    Ask questions about this drug using data from:
    - Mechanism and targets
    - Clinical trials
    - Safety signals
    - Evidence base
    - Real-world sentiment
    """)

    # Initialize chat history
    if 'messages' not in st.session_state:
        st.session_state.messages = []

    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Chat input
    if prompt := st.chat_input("Ask about this drug..."):
        # Add user message to history
        st.session_state.messages.append({"role": "user", "content": prompt})

        with st.chat_message("user"):
            st.markdown(prompt)

        # Generate AI response (placeholder)
        with st.chat_message("assistant"):
            response = f"""
            **Placeholder AI Response**

            You asked: "{prompt}"

            This is where the AI would provide an intelligent response about {drug_name},
            drawing from:
            - Drug scores and mechanism data
            - Recent trial results
            - Safety profile
            - Evidence quality

            The AI chat will be powered by Claude with context injection from our Supabase database.
            """
            st.markdown(response)

        # Add assistant response to history
        st.session_state.messages.append({"role": "assistant", "content": response})

    # Suggested questions
    st.markdown("---")
    st.markdown("**Suggested Questions:**")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("Explain mechanism in simple terms"):
            st.info("Click 'Send' after typing a question")
        if st.button("Compare to similar drugs"):
            st.info("Click 'Send' after typing a question")

    with col2:
        if st.button("What are the main side effects?"):
            st.info("Click 'Send' after typing a question")
        if st.button("Show trial success rate"):
            st.info("Click 'Send' after typing a question")

    st.info("💡 AI chat will be powered by Claude API with context from drug data.")
