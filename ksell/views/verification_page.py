"""Verification Page for KSell Entreprise Gradio UI."""

import gradio as gr

from ksell.services.user_service import UserService


def create_verification_page(user_service: UserService):
    """Create the email verification page."""

    def on_verify(token: str):
        success, message = user_service.verify(token)
        if success:
            return gr.update(visible=True, value=f"✅ {message}")
        else:
            return gr.update(visible=True, value=f"❌ {message}")

    with gr.Column(elem_id="verification-container"):
        gr.Markdown("## 🔐 KSell Entreprise - Verify Account")
        gr.Markdown("Enter the verification code sent to your email address.")

        with gr.Row():
            with gr.Column():
                verify_token = gr.Textbox(
                    label="Verification Code",
                    placeholder="Enter the 6-digit code",
                    info="Check your email for the verification code",
                )
                verify_btn = gr.Button(
                    "✅ Verify", variant="primary", elem_id="verify-btn"
                )

        verify_status = gr.Markdown(visible=False, elem_id="verify-status")

        verify_btn.click(
            fn=on_verify,
            inputs=[verify_token],
            outputs=[verify_status],
        )

    return verify_token, verify_btn
