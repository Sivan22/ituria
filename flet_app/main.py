import flet as ft
from typing import Dict

class State:
    def __init__(self):
        self.api_keys: Dict[str, str] = {
            "google": "",
            "openai": "",
            "anthropic": "",
        }
        self.provider: str = ""
        self.messages = []

    def update_messages(self, messages):
        self.messages = messages

def main(page: ft.Page):
    page.title = "איתוריא"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.rtl = True
    page.horizontal_alignment = ft.CrossAxisAlignment.STRETCH

    state = State()

    def display_messages():
        chat_messages.controls = []
        for msg in state.messages:
            if msg["type"] == "user":
                chat_messages.controls.append(
                    ft.Text(msg["content"], text_align=ft.TextAlign.RIGHT)
                )
            elif msg["type"] == "ai":
                chat_messages.controls.append(
                    ft.Text(msg["content"], text_align=ft.TextAlign.LEFT)
                )
            # Add more conditions for other message types if needed
        page.update()

    def handle_submit(e):
        if not chat_input.value:
            return

        # Add user message to state and display
        state.messages.append({"type": "user", "content": chat_input.value})
        display_messages()

        # Placeholder for handling chat input
        # Here you will need to implement the interaction with the agent
        # and update the chat_messages control
        # For example:
        # state.messages.append({"type": "ai", "content": "Response from agent"})
        # display_messages()

        chat_input.value = ""
        page.update()

    chat_messages = ft.Column(expand=True, scroll=ft.ScrollMode.ADAPTIVE)

    chat_input = ft.TextField(
        label="הזן שאלה", on_submit=handle_submit, expand=True
    )

    # Sidebar controls
    api_key_fields = []
    for provider, label in [
        ("google", "Google API Key"),
        ("openai", "OpenAI API Key"),
        ("anthropic", "Anthropic API Key"),
    ]:
        api_key_fields.append(
            ft.TextField(
                label=label,
                value=state.api_keys[provider],
                password=True,
                can_reveal_password=True,
                on_change=lambda e, p=provider: setattr(
                    state, "api_keys", {**state.api_keys, p: e.control.value}
                ),
            )
        )

    provider_dropdown = ft.Dropdown(
        label="ספק בינה מלאכותית",
        options=[
            ft.dropdown.Option("google", "Google"),
            ft.dropdown.Option("openai", "OpenAI"),
            ft.dropdown.Option("anthropic", "Anthropic"),
        ],
        value=state.provider,
        on_change=lambda e: setattr(state, "provider", e.control.value),
    )

    sidebar = ft.Column([ft.Text("הגדרות"), *api_key_fields, provider_dropdown])

    # Main layout
    page.add(
        ft.Row(
            [
                sidebar,
                ft.Column([chat_messages, ft.Row([chat_input])], expand=True),
            ],
            expand=True,
        )
    )

if __name__ == "__main__":
    ft.app(target=main)
