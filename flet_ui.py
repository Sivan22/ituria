import flet as ft
from document_indexer import DocumentIndexer
from agent_workflow import SearchAgent
import os
from typing import Optional
import time


class SearchAgentUI:
    def __init__(self):
        self.indexer: Optional[DocumentIndexer] = None
        self.agent: Optional[SearchAgent] = None
        self.selected_folder: Optional[str] = None
        self.status_text: Optional[ft.Text] = None
        self.search_field: Optional[ft.TextField] = None
        self.folder_display: Optional[ft.Text] = None
        self.results_column: Optional[ft.Column] = None
        self.page: Optional[ft.Page] = None  # Store page reference
        self.folder_button: Optional[ft.ElevatedButton] = None

    def main(self, page: ft.Page):
        # Store page reference
        self.page = page
        
        # Configure the page
        page.title = "Document Search Agent"
        page.theme_mode = ft.ThemeMode.LIGHT
        page.window_width = 1000
        page.window_height = 800
        page.window_resizable = True

        # Status text for indexing
        self.status_text = ft.Text(
            value="Initializing system...",
            color=ft.colors.GREY_700,
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
            "Select Folder",
            icon=ft.icons.FOLDER_OPEN,
            on_click=pick_folder_click,
            disabled=True,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=8),
                padding=20
            )
        )

        self.folder_display = ft.Text(
            value="No folder selected",
            color=ft.colors.GREY_700,
            size=14,
            weight=ft.FontWeight.W_400
        )

        self.search_field = ft.TextField(
            label="Enter your search query",
            expand=True,
            on_submit=self.on_search,
            disabled=True,
            border_radius=8,
            filled=True,
            prefix_icon=ft.icons.SEARCH,
            hint_text="Type your question here..."
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
                                content=ft.Row(
                                    [
                                        self.folder_button,
                                        ft.Container(width=10),
                                        self.folder_display,
                                    ],
                                    alignment=ft.MainAxisAlignment.START
                                ),
                                margin=ft.margin.only(bottom=20)
                            ),
                            ft.Container(
                                content=self.search_field,
                                margin=ft.margin.only(bottom=20)
                            ),
                            ft.Container(
                                content=self.results_column,
                                border=ft.border.all(1, ft.colors.GREY_300),
                                border_radius=8,
                                padding=10
                            )
                        ]),
                        padding=30
                    ),
                    elevation=3
                ),
                margin=ft.margin.only(top=20)
            )
        )
        self.initialize_system()
        
    def clear_screen(self):
        """Clear all results and reset status"""
        if self.results_column:
            self.results_column.controls = []
        if self.status_text:
            self.status_text.value = ""
        if self.page:
            self.page.update()

    def initialize_system(self):
        """Initialize the indexer and agent at startup"""
        try:
            self.status_text.value = "Initializing document indexer..."
            self.page.update()
            
            # Initialize indexer and agent
            self.indexer = DocumentIndexer()
            self.agent = SearchAgent(self.indexer)
            
            self.status_text.value = "Ready! Select a folder to index documents or start searching."
            # Enable controls after initialization
            self.folder_button.disabled = False          
           
            if self.search_field:
                self.search_field.disabled = False
            self.page.update()
            
        except ConnectionError:
            self.status_text.value = "Error: Could not connect to Elasticsearch. Make sure it's running on localhost:9200"
            self.page.update()
        except Exception as ex:
            self.status_text.value = f"Error initializing system: {str(ex)}"
            self.page.update()

    def on_folder_picked(self, e: ft.FilePickerResultEvent):
        if e.path:
            # Clear previous results
            self.clear_screen()
            
            self.selected_folder = e.path
            self.folder_display.value = f"Selected: {e.path}"
            self.status_text.value = "Indexing documents..."
            e.page.update()
            
            try:
                num_docs = self.indexer.index_documents(e.path)
                self.status_text.value = f"Ready to search! ({num_docs} documents indexed)"
                e.page.update()
            except FileNotFoundError:
                self.status_text.value = "Error: Selected folder not found or inaccessible"
                e.page.update()
            except Exception as ex:
                self.status_text.value = f"Error indexing documents: {str(ex)}"
                e.page.update()

    def on_search(self, e):
        if e.control.value:
            # Clear previous results
            self.clear_screen()
            
            search_text = e.control.value
            # Clear previous results
            self.results_column.controls = []
            e.page.update()
            
            # Perform search
            self.status_text.value = "Searching..."
            e.page.update()
            
            try:
                results = self.agent.search_and_answer(search_text)  

                # Create a container for steps with a title
                steps_container = ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Text(
                                "Search Process Steps",
                                size=20,
                                weight=ft.FontWeight.BOLD,
                                color=ft.colors.BLUE_700
                            ),
                            ft.Divider(height=2, color=ft.colors.BLUE_200)
                        ],
                        spacing=10
                    ),
                    margin=ft.margin.only(bottom=20)
                )
                self.results_column.controls.append(steps_container)

                # Add each step with a timeline-like visualization
                for i, step in enumerate(results['steps']):
                    step_row = ft.Row(
                        controls=[
                            # Timeline connector
                            ft.Container(
                                content=ft.Column([
                                    ft.Container(
                                        content=ft.Text(f"{i+1}", color=ft.colors.WHITE, size=14),
                                        bgcolor=ft.colors.BLUE,
                                        border_radius=50,
                                        width=30,
                                        height=30,
                                        alignment=ft.alignment.center
                                    ),
                                    ft.Container(
                                        bgcolor=ft.colors.BLUE_200,
                                        width=2,
                                        height=40,
                                        visible=i < len(results['steps']) - 1
                                    )
                                ]),
                                padding=ft.padding.only(right=20)
                            ),
                            # Step content
                            ft.Container(
                                content=ft.Column([
                                    ft.Text(
                                        step['action'],
                                        weight=ft.FontWeight.BOLD,
                                        color=ft.colors.BLUE_700,
                                        size=16
                                    ),
                                    ft.Text(
                                        step['description'],
                                        color=ft.colors.GREY_800,
                                        size=14
                                    ),
                                    # Add detailed explanation for evaluation step
                                    ft.Container(
                                        content=ft.Text(
                                            step.get('explanation', ''),
                                            color=ft.colors.GREY_700,
                                            size=12,
                                            italic=True
                                        ),
                                        visible=step['action'].startswith('Result Evaluation')
                                    ),
                                    # Add results display
                                    ft.Container(
                                        content=self._create_results_view(step.get('results', [])),
                                        padding=ft.padding.only(left=20, top=10),
                                        visible=bool(step.get('results'))
                                    )
                                ]),
                                expand=True
                            )
                        ],
                        alignment=ft.MainAxisAlignment.START
                    )
                    steps_container.content.controls.append(step_row)

                # Display final answer in a prominent card
                answer_card = ft.Card(
                    content=ft.Container(
                        content=ft.Column([
                            ft.Text(
                                "Final Answer",
                                weight=ft.FontWeight.BOLD,
                                size=20,
                                color=ft.colors.BLUE_700
                            ),
                            ft.Divider(height=2, color=ft.colors.BLUE_200),
                            ft.Container(
                                content=ft.Column([
                                    ft.Text(
                                        results['answer'],
                                        size=16,
                                        color=ft.colors.GREY_900
                                    ),
                                    # Show suggestion icon and text for no results case
                                    ft.Container(
                                        content=ft.Row([
                                            ft.Icon(
                                                name=ft.icons.LIGHTBULB_OUTLINE,
                                                color=ft.colors.ORANGE_400,
                                                size=20
                                            ),
                                            ft.Text(
                                                "Try using different keywords or rephrasing your question",
                                                color=ft.colors.GREY_700,
                                                italic=True,
                                                size=14
                                            )
                                        ], spacing=10),
                                        visible=not results['sources'],
                                        margin=ft.margin.only(top=20)
                                    )
                                ]),
                                padding=20,
                                bgcolor=ft.colors.BLUE_50 if results['sources'] else ft.colors.ORANGE_50
                            )
                        ]),
                        padding=20
                    ),
                    margin=ft.margin.only(top=20, bottom=20)
                )
                self.results_column.controls.append(answer_card)

                # Display source documents if available
                if results['sources']:
                    sources_container = ft.Container(
                        content=ft.Column(
                            controls=[
                                ft.Text(
                                    "Source Documents",
                                    size=20,
                                    weight=ft.FontWeight.BOLD,
                                    color=ft.colors.BLUE_700
                                ),
                                ft.Divider(height=2, color=ft.colors.BLUE_200)
                            ],
                            spacing=10
                        ),
                        margin=ft.margin.only(top=20, bottom=20)
                    )
                    self.results_column.controls.append(sources_container)

                    # Add each source with expandable highlights
                    for i, source in enumerate(results['sources']):
                        # Create highlights text
                        highlights_text = "\n\n".join(
                            f"...{highlight}..." for highlight in source['highlights']
                        )
                        
                        # Create expandable source card
                        source_card = ft.Card(
                            content=ft.Container(
                                content=ft.Column([
                                    # Source header with expand button
                                    ft.Row([
                                        ft.Icon(
                                            name=ft.icons.DESCRIPTION_OUTLINED,
                                            color=ft.colors.BLUE_700,
                                        ),
                                        ft.Text(
                                            os.path.basename(source['path']),
                                            weight=ft.FontWeight.BOLD,
                                            color=ft.colors.BLUE_700,
                                            size=16,
                                            expand=True
                                        ),
                                        ft.Container(
                                            content=ft.Text(
                                                f"Score: {source['score']:.2f}",
                                                color=ft.colors.GREY_700,
                                                size=14
                                            ),
                                            margin=ft.margin.only(right=10)
                                        ),
                                        ft.IconButton(
                                            icon=ft.icons.EXPAND_MORE,
                                            icon_color=ft.colors.BLUE_700,
                                            data=f"source_{i}",
                                            on_click=lambda e: self.toggle_source_expansion(e)
                                        )
                                    ]),
                                    # Path display
                                    ft.Container(
                                        content=ft.Text(
                                            source['path'],
                                            color=ft.colors.GREY_700,
                                            size=12,
                                            italic=True
                                        ),
                                        margin=ft.margin.only(left=30, bottom=10)
                                    ),
                                    # Expandable highlights section
                                    ft.Container(
                                        content=ft.Column([
                                            ft.Text(
                                                "Relevant Excerpts:",
                                                weight=ft.FontWeight.BOLD,
                                                color=ft.colors.BLUE_700,
                                                size=14
                                            ),
                                            ft.Container(
                                                content=ft.Text(
                                                    highlights_text,
                                                    color=ft.colors.GREY_800,
                                                    size=14
                                                ),
                                                bgcolor=ft.colors.BLUE_50,
                                                padding=10,
                                                border_radius=5
                                            )
                                        ]),
                                        visible=False,
                                        data=f"source_content_{i}"
                                    )
                                ]),
                                padding=15
                            ),
                            margin=ft.margin.only(bottom=10)
                        )
                        sources_container.content.controls.append(source_card)

                self.status_text.value = "Search completed!"
                
            except Exception as err:
                self.status_text.value = f"Error: {str(err)}"
                error_card = ft.Card(
                    content=ft.Container(
                        content=ft.Text(f"Error occurred: {str(err)}", color=ft.colors.RED),
                        padding=10
                    )
                )
                self.results_column.controls.append(error_card)
            
            e.page.update()

    def toggle_source_expansion(self, e):
        """Toggle the visibility of source content when expand button is clicked"""
        source_id = e.control.data  # e.g., "source_0"
        content_id = f"source_content_{source_id.split('_')[1]}"  # e.g., "source_content_0"
        
        # Find the content container
        for control in self.results_column.controls:
            if isinstance(control, ft.Container) and control.content and isinstance(control.content, ft.Column):
                for card in control.content.controls:
                    if isinstance(card, ft.Card):
                        for container in card.content.content.controls:
                            if (isinstance(container, ft.Container) and 
                                container.data == content_id):
                                # Toggle visibility
                                container.visible = not container.visible
                                # Update icon
                                for row in card.content.content.controls:
                                    if isinstance(row, ft.Row):
                                        for button in row.controls:
                                            if (isinstance(button, ft.IconButton) and 
                                                button.data == source_id):
                                                button.icon = (ft.icons.EXPAND_LESS 
                                                             if container.visible 
                                                             else ft.icons.EXPAND_MORE)
                                                break
                                break
        
        e.page.update()

    def toggle_highlights(self, e, highlights_container):
        """Toggle visibility of highlights container and update button icon"""
        highlights_container.visible = not highlights_container.visible
        e.control.icon = ft.icons.EXPAND_LESS if highlights_container.visible else ft.icons.EXPAND_MORE
        e.control.tooltip = "Hide highlights" if highlights_container.visible else "Show highlights"
        e.page.update()

    def _create_results_view(self, results):
        """Create a visual representation of step results"""
        result_widgets = []
        
        for result in results:
            if result['type'] == 'keywords':
                # Display keywords as chips
                result_widgets.append(
                    ft.Row(
                        controls=[
                            ft.Container(
                                content=ft.Text(keyword, size=12),
                                bgcolor=ft.colors.BLUE_50,
                                padding=ft.padding.all(5),
                                border_radius=15
                            )
                            for keyword in result['content']
                        ],
                        wrap=True,
                        spacing=5
                    )
                )
            
            elif result['type'] == 'document':
                # Display document result with title and expandable highlights
                content = result['content']
                
                # Container for all highlights
                highlights_container = ft.Container(
                    content=ft.Column([
                        ft.Text(
                            highlight,
                            size=11,
                            color=ft.colors.GREY_800,
                        ) for highlight in content['highlights']
                    ]),
                    visible=False,  # Initially hidden
                )
                
                # Create expand button
                expand_button = ft.IconButton(
                    icon=ft.icons.EXPAND_MORE,
                    icon_size=20,
                    tooltip="Show highlights",
                    on_click=lambda e, h=highlights_container: self.toggle_highlights(e, h)
                )
                
                result_widgets.append(
                    ft.Container(
                        content=ft.Column([
                            ft.Row([
                                ft.Text(f" {content['title']}", 
                                       size=12, 
                                       weight=ft.FontWeight.BOLD,
                                       expand=True),
                                ft.Text(f"Score: {content['score']}", 
                                       size=11, 
                                       color=ft.colors.GREY_700,
                                       weight=ft.FontWeight.BOLD),
                                expand_button,
                            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                            highlights_container,
                        ]),
                        padding=ft.padding.all(10),
                        border=ft.border.all(1, ft.colors.BLUE_100),
                        border_radius=5,
                        margin=ft.margin.only(bottom=5)
                    )
                )
            
            elif result['type'] == 'evaluation':
                # Display evaluation status
                content = result['content']
                icon = ft.icons.CHECK_CIRCLE if content['status'] == 'accepted' else ft.icons.REFRESH
                color = ft.colors.GREEN_400 if content['status'] == 'accepted' else ft.colors.ORANGE_400
                result_widgets.append(
                    ft.Row([
                        ft.Icon(icon, color=color, size=16),
                        ft.Text(
                            f"Confidence: {content['confidence']}",
                            color=color,
                            size=12
                        )
                    ])
                )
            
            elif result['type'] == 'next_keywords':
                # Display next keywords to try
                result_widgets.append(
                    ft.Container(
                        content=ft.Column([
                            ft.Text("Trying next:", size=11, color=ft.colors.GREY_700),
                            ft.Row(
                                controls=[
                                    ft.Container(
                                        content=ft.Text(keyword, size=11),
                                        bgcolor=ft.colors.BLUE_50,
                                        padding=ft.padding.all(5),
                                        border_radius=15
                                    )
                                    for keyword in result['content']
                                ],
                                wrap=True,
                                spacing=5
                            )
                        ])
                    )
                )
        
        return ft.Column(controls=result_widgets, spacing=5)



if __name__ == "__main__":
    app = SearchAgentUI()
    ft.app(target=app.main)
