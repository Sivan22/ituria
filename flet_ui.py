import flet as ft
from tantivy_search_agent import TantivySearchAgent
from agent_workflow import SearchAgent
import os
from typing import Optional


class SearchAgentUI:
    def __init__(self):
        self.tantivy_agent: Optional[TantivySearchAgent] = None
        self.agent: Optional[SearchAgent] = None
        self.selected_folder: Optional[str] = None
        self.status_text: Optional[ft.Text] = None
        self.search_field: Optional[ft.TextField] = None
        self.folder_display: Optional[ft.Text] = None
        self.results_column: Optional[ft.Column] = None
        self.page: Optional[ft.Page] = None  # Store page reference
        self.folder_button: Optional[ft.ElevatedButton] = None
        self.results_per_search: Optional[ft.TextField] = None
        self.max_iterations: Optional[ft.TextField] = None
        self.provider_dropdown: Optional[ft.Dropdown] = None
        self.steps_container: Optional[ft.Container] = None
        self.answer_card: Optional[ft.Card] = None
        self.sources_container: Optional[ft.Container] = None

    def main(self, page: ft.Page):
        # Store page reference
        self.page = page
        
        # Configure the page
        page.title = "איתוריא"
        page.theme_mode = ft.ThemeMode.LIGHT
        page.window.width = 1000
        page.window.height = 800
        page.window.resizable = True
        page.rtl = True  # Set RTL direction for the entire page

        # Create a temporary agent to get available providers
        temp_agent = SearchAgent(None)
        available_providers = temp_agent.get_available_providers()        

        # Provider selection dropdown
        self.provider_dropdown = ft.Dropdown(
            label="ספק בינה מלאכותית",
            value=available_providers[0] if available_providers else None,
            options=[ft.dropdown.Option(provider) for provider in available_providers],
            width=200,
            on_change=lambda e: self.agent.set_provider(e.control.value) if self.agent else None
        )

        # the max number of iterations
        self.max_iterations = ft.TextField(
            label="מספר נסיונות מקסימלי",
            value="3",
            width=150,
            text_align=ft.TextAlign.LEFT,  # In RTL, LEFT alignment will appear on the right
            keyboard_type=ft.KeyboardType.NUMBER,
        )

        # the number of results per search
        self.results_per_search = ft.TextField(
            label="תוצאות לכל חיפוש",
            value="5",
            width=150,
            text_align=ft.TextAlign.LEFT,  # In RTL, LEFT alignment will appear on the right
            keyboard_type=ft.KeyboardType.NUMBER,
        )

        # Status text for indexing
        self.status_text = ft.Text(
            value="אנא בחר תיקיית אינדקס כדי להתחיל בחיפוש",
            color=ft.Colors.GREY_700,
            size=16,
            weight=ft.FontWeight.W_500
        )

        # Directory picker
        folder_picker = ft.FilePicker(
            on_result=self.on_folder_picked
        )
        page.overlay.append(folder_picker)

        def pick_folder_click(e):
            folder_picker.get_directory_path()

        self.folder_button = ft.ElevatedButton(
            "בחר תיקיית אינדקס",
            icon=ft.icons.FOLDER_OPEN,
            on_click=pick_folder_click,
            disabled=False,  # Enable immediately since we need folder selection first
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=8),
                padding=20
            )
        )

        self.folder_display = ft.Text(
            value="לא נבחרה תיקיית אינדקס",
            color=ft.Colors.GREY_700,
            size=14,
            weight=ft.FontWeight.W_400
        )

        self.search_field = ft.TextField(
            label="הכנס שאילתת חיפוש",
            expand=True,
            on_submit=self.on_search,
            disabled=True,
            border_radius=8,
            filled=True,
            prefix_icon=ft.icons.SEARCH,
            hint_text="הקלד את שאילתת החיפוש שלך כאן...",
            text_align=ft.TextAlign.RIGHT,
        )
 
        # Results display
        self.results_column = ft.Column(
            scroll=ft.ScrollMode.AUTO,
            spacing=10,
            height=500
        )

        # Layout with Container and Card
        page.add(
            ft.Container(
                content=ft.Card(
                    content=ft.Container(
                        content=ft.Column([
                            ft.Container(
                                content=self.status_text,
                                margin=ft.margin.only(bottom=20)
                            ),
                            ft.Container(
                                content=ft.Column([
                                    ft.Row(
                                        controls=[
                                            self.folder_button,
                                            ft.Container(expand=True),
                                            self.provider_dropdown,
                                            self.max_iterations,
                                            self.results_per_search,
                                        ],
                                        alignment=ft.MainAxisAlignment.START,
                                    ),
                                ]),
                                margin=ft.margin.only(bottom=20)
                            ),
                            ft.Container(
                                content=self.search_field,
                                margin=ft.margin.only(bottom=20)
                            ),
                            ft.Container(
                                content=self.results_column,
                                expand=True
                            )
                        ]),
                        padding=30
                    ),
                    elevation=4
                ),
                padding=20,
                expand=True
            )
        )
        
    def clear_screen(self):
        """Clear all results and reset status"""
        if self.results_column:
            self.results_column.controls.clear()
            self.page.update()

    def initialize_system(self):
        """This method is no longer needed as we're using Tantivy directly"""
        pass

    def on_folder_picked(self, e: ft.FilePickerResultEvent):
        if e.path:
            self.selected_folder = e.path
            self.folder_display.value = f"אינדקס נבחר: {os.path.basename(e.path)}"
            try:
                # Initialize both Tantivy agent and search agent
                self.tantivy_agent = TantivySearchAgent(e.path)
                if self.tantivy_agent.validate_index():
                    # Create search agent with Tantivy agent
                    self.agent = SearchAgent(
                        self.tantivy_agent,
                        provider_name=self.provider_dropdown.value
                    )
                    self.status_text.value = "האינדקס נטען בהצלחה! מוכן לחיפוש."
                    self.status_text.color = ft.Colors.GREEN
                    self.search_field.disabled = False
                else:
                    self.status_text.value = "תיקיית אינדקס לא תקינה. אנא בחר אינדקס תקין."
                    self.status_text.color = ft.Colors.RED
                    self.search_field.disabled = True
            except Exception as ex:
                self.status_text.value = f"שגיאה בטעינת האינדקס: {str(ex)}"
                self.status_text.color = ft.Colors.RED
                self.search_field.disabled = True
        else:
            self.status_text.value = "לא נבחרה תיקייה"
            self.status_text.color = ft.Colors.GREY_700
            self.search_field.disabled = True
            
        self.page.update()

    def handle_step_update(self, step):
        """Handle streaming updates from the search process"""
        try:
            # Initialize containers if this is the first step
            if not self.steps_container:
                self.steps_container = ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Text(
                                "צעדי תהליך החיפוש",
                                size=20,
                                weight=ft.FontWeight.BOLD,
                                color=ft.Colors.BLUE_700
                            ),
                            ft.Divider(height=2, color=ft.Colors.BLUE_200)
                        ],
                        spacing=10
                    ),
                    margin=ft.margin.only(bottom=20)
                )
                self.results_column.controls.append(self.steps_container)

            # Check if this is the final result
            if 'final_result' in step:
                final_result = step['final_result']
                
                # Add answer card
                self.answer_card = ft.Card(
                    content=ft.Container(
                        content=ft.Column([
                            ft.Text(
                                "תשובה סופית",
                                weight=ft.FontWeight.BOLD,
                                size=20,
                                color=ft.Colors.BLUE_700
                            ),
                            ft.Divider(height=2, color=ft.Colors.BLUE_200),
                            ft.Container(
                                content=ft.Text(
                                    final_result['answer'],
                                    size=16,
                                    color=ft.Colors.GREY_900
                                ),
                                padding=20,
                                bgcolor=ft.Colors.BLUE_50
                            )
                        ]),
                        padding=20
                    ),
                    margin=ft.margin.only(top=20, bottom=20)
                )
                self.results_column.controls.append(self.answer_card)

                # Add sources if available
                if final_result['sources']:
                    self.sources_container = ft.Container(
                        content=ft.Column([
                            ft.Text(
                                "מסמכי מקור",
                                size=20,
                                weight=ft.FontWeight.BOLD,
                                color=ft.Colors.BLUE_700
                            ),
                            ft.Divider(height=2, color=ft.Colors.BLUE_200),
                            ft.ExpansionPanelList(
                                expand_icon_color=ft.colors.BLUE,
                                elevation=2,
                                controls=[
                                    ft.ExpansionPanel(
                                        header=ft.ListTile(
                                            title=ft.Text(
                                                source['title'],
                                                weight=ft.FontWeight.BOLD,
                                                size=16,
                                                color=ft.Colors.BLUE_700
                                            ),
                                            subtitle=ft.Column([
                                                ft.Text(
                                                    f"ציון: {source['score']:.2f}",
                                                    size=14,
                                                    color=ft.Colors.GREY_700
                                                ),
                                                ft.Text(
                                                    source['path'],
                                                    size=12,
                                                    color=ft.Colors.GREY_600,
                                                    italic=True
                                                ),
                                            ]),
                                        ),
                                        content=ft.Container(
                                            content=ft.Column([
                                                ft.Text(
                                                    highlight,
                                                    size=14,
                                                    color=ft.Colors.GREY_800
                                                ) for highlight in source['highlights']
                                            ]),
                                            bgcolor=ft.Colors.BLUE_50,
                                            padding=10,
                                            border_radius=5,
                                        ),
                                        expanded=False,
                                    )
                                    for source in final_result['sources']
                                ]
                            )
                        ]),
                        margin=ft.margin.only(bottom=20)
                    )
                    self.results_column.controls.append(self.sources_container)

                self.status_text.value = "חיפוש הושלם!"
                self.status_text.color = ft.Colors.GREEN
            else:
                # Add the step to the steps container
                step_number = len(self.steps_container.content.controls) - 2  # Subtract title and divider
                step_row = ft.Row(
                    controls=[
                        # Timeline connector
                        ft.Container(
                            content=ft.Column(
                                [ft.Container(
                                    content=ft.Text(f"{step_number + 1}", color=ft.Colors.WHITE, size=14),
                                    bgcolor=ft.Colors.BLUE,
                                    border_radius=50,
                                    width=30,
                                    height=30,
                                    alignment=ft.alignment.center
                                ),
                                ft.Container(
                                    bgcolor=ft.Colors.BLUE_200,
                                    width=2,
                                    height=30,
                                    visible=True  # Always visible during streaming
                                )],
                            alignment=ft.MainAxisAlignment.START),
                            padding=ft.padding.only(right=20),
                        ),
                        # Step content
                        ft.Container(
                            content=ft.Column([
                                ft.Text(
                                    step['action'],
                                    weight=ft.FontWeight.BOLD,
                                    color=ft.Colors.BLUE_700,
                                    size=16
                                ),
                                ft.Text(
                                    step['description'],
                                    color=ft.Colors.GREY_800,
                                    size=14
                                ),
                                self._create_results_view(step.get('results', []))
                            ]),
                            expand=True
                        )
                    ],
                    alignment=ft.MainAxisAlignment.START
                )
                self.steps_container.content.controls.append(step_row)

            self.page.update()

        except Exception as ex:
            self.status_text.value = f"שגיאה בעדכון הממשק: {str(ex)}"
            self.status_text.color = ft.Colors.RED
            self.page.update()

    def on_search(self, e):
        if not self.agent or not self.tantivy_agent:
            self.status_text.value = "אנא בחר תיקיית אינדקס תקינה תחילה"
            self.status_text.color = ft.Colors.RED
            self.page.update()
            return

        query = self.search_field.value
        if not query:
            return

        self.status_text.value = "מחפש..."
        self.status_text.color = ft.Colors.BLUE
        self.clear_screen()
        
        # Reset containers
        self.steps_container = None
        self.answer_card = None
        self.sources_container = None
        
        self.page.update()

        try:
            # Use the streaming search process
            self.agent.search_and_answer(
                query=query,
                num_results=int(self.results_per_search.value),
                max_iterations=int(self.max_iterations.value),
                on_step=self.handle_step_update
            )
            
        except Exception as ex:
            self.status_text.value = f"שגיאת חיפוש: {str(ex)}"
            self.status_text.color = ft.Colors.RED
            self.results_column.controls.clear()
            self.results_column.controls.append(
                ft.Text(f"שגיאה בביצוע חיפוש: {str(ex)}", 
                       size=16, 
                       color=ft.Colors.RED)
            )
            self.page.update()

    def _create_results_view(self, results):
        """Create a visual representation of step results"""
        if not results:
            return ft.Container(
                content=ft.Text(
                    "לא נמצאו תוצאות",
                    size=14,
                    weight=ft.FontWeight.BOLD,
                    color=ft.Colors.RED_400
                ),
                padding=10,
                border=ft.border.all(1, ft.Colors.RED_200),
                border_radius=5,
                margin=ft.margin.only(bottom=5),
                bgcolor=ft.Colors.RED_50
            )
        
        result_widgets = []
        document_results = []
        
        for result in results:
            if result['type'] == 'query':
                # Display keywords as chips
                result_widgets.append(
                    ft.Text(
                        f"שאילתת חיפוש נוצרה: {result['content']}",
                        size=12,
                        color=ft.Colors.GREY_700,
                        text_align=ft.TextAlign.RIGHT,
                    )
                )
                
            elif result['type'] == 'document':
                # Collect document results
                content = result['content']
                document_results.append(
                    ft.Container(
                        content=ft.Column([
                            ft.Row([
                                ft.Text(
                                    content['title'],
                                    size=12,
                                    weight=ft.FontWeight.BOLD,
                                    expand=True
                                ),
                                ft.Text(
                                    f"ציון: {content['score']:.2f}",
                                    size=11,
                                    color=ft.Colors.GREY_700,
                                    weight=ft.FontWeight.BOLD,
                                    text_align=ft.TextAlign.RIGHT,
                                ),
                            ]),
                            ft.Container(
                                content=ft.Column([
                                    ft.Text(
                                        content['highlights'][0],
                                        size=11,
                                        color=ft.Colors.GREY_800
                                    )
                                ]),
                                bgcolor=ft.Colors.BLUE_50,
                                padding=10,
                                border_radius=5,
                                margin=ft.margin.only(top=5)
                            )
                        ]),
                        padding=ft.padding.all(10),
                        border=ft.border.all(1, ft.Colors.BLUE_100),
                        border_radius=5,
                        margin=ft.margin.only(bottom=5)
                    )
                )
                
            elif result['type'] == 'evaluation':
                # Display evaluation status
                content = result['content']
                icon = ft.icons.CHECK_CIRCLE if content['status'] == 'accepted' else ft.icons.REFRESH
                color = ft.Colors.GREEN_400 if content['status'] == 'accepted' else ft.Colors.ORANGE_400
                result_widgets.append(
                    ft.Row([
                        ft.Icon(icon, color=color, size=16),
                        ft.Text(
                            f"ביטחון: {content['confidence']}",
                            color=color,
                            size=12,
                            text_align=ft.TextAlign.RIGHT,
                        )]))
                if content['explanation']:
                    result_widgets.append(
                        ft.Text(
                            content['explanation'],
                            size=11,
                            color=ft.Colors.GREY_700
                        )
                )
            
            elif result['type'] == 'new_query':
                # Display next keywords to try
                result_widgets.append(
                    ft.Container(
                        content=ft.Column([
                            ft.Text(f"ניסיון הבא: {result['content']}", 
                                   size=11, 
                                   color=ft.Colors.GREY_700,
                                   text_align=ft.TextAlign.RIGHT),
                        ])
                    )
                )
        
        if document_results:
            # Create a single collapsible container for all documents
            documents_container = ft.Container(
                content=ft.Column(document_results),
                visible=False  # Initially hidden
            )
            
            # Create an expandable header for all documents
            documents_header = ft.Container(
                content=ft.Row([
                    ft.IconButton(
                        icon=ft.icons.ARROW_DROP_DOWN,
                        on_click=lambda e, dc=documents_container: self._toggle_document_visibility(e, dc)
                    ),
                    ft.Text(
                        f"נמצאו {len(document_results)} תוצאות",
                        size=14,
                        weight=ft.FontWeight.BOLD,
                        color=ft.Colors.BLUE_700
                    )
                ]),
                padding=10,
                border=ft.border.all(1, ft.Colors.BLUE_200),
                border_radius=5,
                margin=ft.margin.only(bottom=5),
                bgcolor=ft.Colors.BLUE_50
            )
            
            result_widgets.extend([documents_header, documents_container])
    
        return ft.Column(controls=result_widgets, spacing=5)

    def _toggle_document_visibility(self, e, document_container):
        """Toggle the visibility of document results"""
        document_container.visible = not document_container.visible
        # Update the icon based on the container's visibility
        e.control.icon = ft.icons.ARROW_DROP_UP if document_container.visible else ft.icons.ARROW_DROP_DOWN
        self.page.update()


if __name__ == "__main__":
    app = SearchAgentUI()
    ft.app(target=app.main)
