"""Profile Page for KSell Entreprise Gradio UI.

User profile management with stats, cards, tools, and subscribers.
"""

import gradio as gr

from services.game_service import GameService
from services.user_service import UserService
from utils.helpers import format_fortune


def create_profile_page(game_service: GameService, user_service: UserService):
    """Create the profile page with user stats and management."""

    def on_view_profile():
        status = game_service.get_player_status()
        if "error" in status:
            return gr.update(visible=True, value=f"❌ {status['error']}")

        md = f"""
**👤 Profile: {status['pseudo']}**

| Stat | Value |
|------|-------|
| 💰 Fortune | {format_fortune(status['fortune'])} |
| ⭐ Stars | {status['etoiles']} |
| 🎮 Competitions | {status['competitions']} |
| 👥 Subscribers | {status['abonnes']} |
| 🃏 Cards | {len(status['cartes'])} |
| 🔧 Tools | {len(status['outils'])} |
| 📦 Total Capacity | {status['total_capacity']:,} units |
| 🏆 Rank | #{status['rank']} |

**🔧 Tools:**
{chr(10).join(f'- {t["nom"]} (Capacity: {t["capacite"]:,})' for t in status['outils']) or '- None'}

**🃏 Cards:**
{', '.join(status['cartes']) if status['cartes'] else '- None'}
"""
        return gr.update(visible=True, value=md)

    def on_update_profile(email: str, profil: str, pays: str):
        success, message = user_service.update_profile(
            pseudo=user_service.get_current_user().pseudo if user_service.get_current_user() else "",
            email=email,
            profil=profil,
            pays=pays,
        )
        if success:
            return gr.update(visible=True, value=f"✅ {message}")
        else:
            return gr.update(visible=True, value=f"❌ {message}")

    with gr.Column(elem_id="profile-container"):
        gr.Markdown("## 👤 KSell Entreprise - Profile")
        gr.Markdown("View and manage your player profile, stats, and inventory.")

        view_btn = gr.Button("👁️ View Profile", variant="primary", elem_id="view-profile-btn")
        profile_display = gr.Markdown(visible=False, elem_id="profile-display")

        # Profile update section
        with gr.Accordion("✏️ Update Profile", open=False):
            with gr.Row():
                with gr.Column():
                    update_email = gr.Textbox(
                        label="Email",
                        placeholder="New email address",
                        info="Leave blank to keep current",
                    )
                    update_profil = gr.Dropdown(
                        choices=["Entrepreneur", "Investisseur", "Spéculateur", "Négociant"],
                        label="Profile Type",
                        info="Your business role",
                    )
                    update_pays = gr.Textbox(
                        label="Country",
                        placeholder="New country",
                        info="Leave blank to keep current",
                    )
                with gr.Column():
                    update_btn = gr.Button("💾 Save Changes", variant="secondary", elem_id="save-profile-btn")

        update_status = gr.Markdown(visible=False, elem_id="update-status")

        # Event handlers
        view_btn.click(
            fn=on_view_profile,
            inputs=[],
            outputs=[profile_display],
        )

        update_btn.click(
            fn=on_update_profile,
            inputs=[update_email, update_profil, update_pays],
            outputs=[update_status],
        )

    return view_btn, update_btn
