import flet as ft
from document_indexer import DocumentIndexer
from agent_workflow import SearchAgent
import os
from typing import Optional
import time
from anthropic import RateLimitError  # Import RateLimitError from anthropic

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

    def clear_screen(self):
        """Clear all results and reset status"""
        if self.results_column:
            self.results_column.controls = []
        if self.status_text:
            self.status_text.value = ""
        if self.page:
            self.page.update()

    def on_folder_picked(self, e: ft.FilePickerResultEvent):
        if e.path:
            # Clear previous results
            self.clear_screen()
            
            self.selected_folder = e.path
            self.folder_display.value = f"Selected: {e.path}"
            self.status_text.value = "Initializing document indexer..."
            e.page.update()
            
            try:
                # Initialize indexer and agent
                self.indexer = DocumentIndexer()
                
                self.status_text.value = "Indexing documents..."
                e.page.update()
                
                try:
                    num_docs = self.indexer.index_documents(e.path)
                    self.agent = SearchAgent(self.indexer)
                    
                    self.status_text.value = f"Ready to search! ({num_docs} documents indexed)"
                    self.search_field.disabled = False
                    e.page.update()
                except FileNotFoundError:
                    self.status_text.value = "Error: Selected folder not found or inaccessible"
                    e.page.update()
                except Exception as ex:
                    self.status_text.value = f"Error indexing documents: {str(ex)}"
                    e.page.update()
                    
            except ConnectionError:
                self.status_text.value = "Error: Could not connect to Elasticsearch. Make sure it's running on localhost:9200"
                e.page.update()
            except Exception as ex:
                self.status_text.value = f"Error initializing indexer: {str(ex)}"
                e.page.update()

    async def on_search(self, e):
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
                                ])
                            )
                        ]),
                        padding=20,
                        bgcolor=ft.colors.BLUE_50 if results['sources'] else ft.colors.ORANGE_50
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

    def main(self, page: ft.Page):
        # Store page reference
        self.page = page
        
        # Configure the page
        page.title = "Document Search Agent"
        page.theme_mode = ft.ThemeMode.LIGHT
        page.padding = 20
        page.window_width = 1000
        page.window_height = 800
        page.window_resizable = True

        # Status text for indexing
        self.status_text = ft.Text(
            value="Please select a folder to index",
            color=ft.colors.GREY_700,
            size=14
        )

        # Directory picker
        folder_picker = ft.FilePicker(
            on_result=self.on_folder_picked
        )
        page.overlay.append(folder_picker)

        def pick_folder_click(e):
            folder_picker.get_directory_path()

        folder_button = ft.ElevatedButton(
            "Select Folder",
            icon=ft.icons.FOLDER_OPEN,
            on_click=pick_folder_click
        )

        self.folder_display = ft.Text(
            value="No folder selected",
            color=ft.colors.GREY_700,
            size=14
        )

        self.search_field = ft.TextField(
            label="Ask a question",
            hint_text="Enter your question here...",
            width=600,
            on_submit=self.on_search,
            disabled=True
        )

        search_button = ft.IconButton(
            icon=ft.icons.SEARCH,
            on_click=lambda e: self.on_search(ft.ControlEvent(self.search_field)),
            disabled=False
        )

        # Results display
        self.results_column = ft.Column(
            scroll=ft.ScrollMode.AUTO,
            spacing=10,
            height=500
        )

        # Layout
        page.add(
            ft.Row([folder_button, self.folder_display], alignment=ft.MainAxisAlignment.START),
            self.status_text,
            ft.Divider(),
            ft.Row(
                [self.search_field, search_button],
                alignment=ft.MainAxisAlignment.CENTER
            ),
            ft.Divider(),
            self.results_column
        )

if __name__ == "__main__":
    app = SearchAgentUI()
    ft.app(target=app.main)
