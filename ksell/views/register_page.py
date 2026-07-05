"""Registration Page for KSell Entreprise Gradio UI."""

import gradio as gr

from ksell.services.user_service import UserService
from ksell.utils.helpers import get_country_list, get_profile_options, get_gender_options


def create_register_page(user_service: UserService):
    """Create the registration page with all user fields."""

    countries = get_country_list()
    country_options = [(c["text"], c["value"]) for c in countries]
    gender_options = get_gender_options()
    profile_options = get_profile_options()

    def on_register(username, password, email, country, birth_date, gender, profile):
        success, message = user_service.register(
            username=username,
            password=password,
            email=email,
            country=country,
            birth_date=birth_date,
            gender=gender,
            profile=profile,
        )
        if success:
            return gr.update(visible=True, value=f"✅ {message}")
        else:
            return gr.update(visible=True, value=f"❌ {message}")

    with gr.Column(elem_id="register-container"):
        gr.Markdown("## 📝 KSell Entreprise - Register")
        gr.Markdown("Create your account to start playing the business simulation game.")

        with gr.Row():
            with gr.Column():
                reg_username = gr.Textbox(
                    label="Username",
                    placeholder="Min 5 characters",
                    info="Minimum 5 characters required",
                )
                reg_password = gr.Textbox(
                    label="Password",
                    placeholder="Min 8 characters",
                    type="password",
                    info="Minimum 8 characters required",
                )
                reg_email = gr.Textbox(
                    label="Email",
                    placeholder="your@email.com",
                    info="Valid email required for verification",
                )
                reg_birth_date = gr.Textbox(
                    label="Date of Birth",
                    placeholder="YYYY-MM-DD",
                    info="Format: YYYY-MM-DD",
                )

            with gr.Column():
                reg_country = gr.Dropdown(
                    choices=country_options,
                    label="Country",
                    info="Select your country",
                    interactive=True,
                )
                reg_gender = gr.Radio(
                    choices=gender_options,
                    label="Gender",
                    value=gender_options[0] if gender_options else None,
                )
                reg_profile = gr.Dropdown(
                    choices=profile_options,
                    label="Profile Type",
                    value=profile_options[0] if profile_options else None,
                    info="Your business role in the game",
                )

        reg_btn = gr.Button("🚀 Create Account", variant="primary", elem_id="register-btn")
        reg_status = gr.Markdown(visible=False, elem_id="register-status")

        reg_btn.click(
            fn=on_register,
            inputs=[reg_username, reg_password, reg_email, reg_country, reg_birth_date, reg_gender, reg_profile],
            outputs=[reg_status],
        )

    return reg_username, reg_password, reg_email, reg_country, reg_birth_date, reg_gender, reg_profile, reg_btn
