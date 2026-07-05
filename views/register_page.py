"""Registration Page for KSell Entreprise Gradio UI."""

import gradio as gr

from services.user_service import UserService
from utils.helpers import get_country_list, get_profil_options, get_sexe_options


def create_register_page(user_service: UserService):
    """Create the registration page with all user fields."""

    countries = get_country_list()
    pays_options = [(c["text"], c["value"]) for c in countries]
    sexe_options = get_sexe_options()
    profil_options = get_profil_options()

    def on_register(pseudo, password, mail, pays, date_naissance, sexe, profil):
        success, message = user_service.register(
            pseudo=pseudo,
            password=password,
            mail=mail,
            pays=pays,
            date_naissance=date_naissance,
            sexe=sexe,
            profil=profil,
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
                reg_pseudo = gr.Textbox(
                    label="Pseudo (Username)",
                    placeholder="Min 5 characters",
                    info="Minimum 5 characters required",
                )
                reg_password = gr.Textbox(
                    label="Password",
                    placeholder="Min 8 characters",
                    type="password",
                    info="Minimum 8 characters required",
                )
                reg_mail = gr.Textbox(
                    label="Email",
                    placeholder="your@email.com",
                    info="Valid email required for verification",
                )
                reg_date = gr.Textbox(
                    label="Date of Birth",
                    placeholder="YYYY-MM-DD",
                    info="Format: YYYY-MM-DD",
                )

            with gr.Column():
                reg_pays = gr.Dropdown(
                    choices=pays_options,
                    label="Country",
                    info="Select your country",
                    interactive=True,
                )
                reg_sexe = gr.Radio(
                    choices=sexe_options,
                    label="Gender",
                    value=sexe_options[0] if sexe_options else None,
                )
                reg_profil = gr.Dropdown(
                    choices=profil_options,
                    label="Profile Type",
                    value=profil_options[0] if profil_options else None,
                    info="Your business role in the game",
                )

        reg_btn = gr.Button("🚀 Create Account", variant="primary", elem_id="register-btn")
        reg_status = gr.Markdown(visible=False, elem_id="register-status")

        reg_btn.click(
            fn=on_register,
            inputs=[reg_pseudo, reg_password, reg_mail, reg_pays, reg_date, reg_sexe, reg_profil],
            outputs=[reg_status],
        )

    return reg_pseudo, reg_password, reg_mail, reg_pays, reg_date, reg_sexe, reg_profil, reg_btn
