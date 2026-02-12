#!/usr/bin/env python3

"""
HTML Injection Example Plugin for An Otter Wiki

This is an example plugin that demonstrates the new HTML injection, link processing, image processing, and heading processing hooks.

Features:
- Injects HTML into the head and body sections
- Adds a CSS class 'exampleClass' to all links
- Sets alt attribute to 'example alt' for all images
- Adds a CSS class 'exampleHeading' to all headings

This plugin demonstrates:
1. template_html_head_inject - Inject content into <head>
2. template_html_body_inject - Inject content into <body>
3. renderer_process_link - Process links during markdown rendering
4. renderer_process_image - Process images during markdown rendering
5. renderer_process_heading - Process headings during markdown rendering
"""

from bs4 import BeautifulSoup
from otterwiki.plugins import hookimpl, plugin_manager


class HtmlInjectionExample:
    """
    Example plugin demonstrating HTML injection and renderer processing hooks.
    """

    @hookimpl
    def setup(self, app, db, storage):
        """Initialize the plugin with the core objects."""
        self.app = app
        self.db = db
        self.storage = storage

    @hookimpl
    def template_html_head_inject(self, page):
        """
        Inject HTML content into the head section.
        In this example let's add some styling for example classes.
        """
        return '''
    <!-- HTML Injection Example Plugin - Head Content -->
    <style>
        .exampleClass {
            border-bottom: 1px dotted #007bff;
            text-decoration: none;
        }
        .exampleClass:hover {
            border-bottom-style: solid;
        }
        .exampleHeading {
            border-left: 4px solid #007bff;
            padding-left: 10px;
            margin-left: -14px;
        }
    </style>
'''

    @hookimpl
    def template_html_body_inject(self, page):
        """
        Inject HTML content into the body section.
        """
        return '<!-- HTML Injection Example Plugin - Body Content -->'

    @hookimpl
    def renderer_process_link(
        self, link_html, link_url, link_text, link_title, page
    ):
        """
        Adds `exampleClass` to classes for links during markdown rendering.
        """
        soup = BeautifulSoup(link_html, 'html.parser')
        link_tag = soup.find('a')

        if link_tag:
            existing_classes = link_tag.get('class', [])
            if isinstance(existing_classes, str):
                existing_classes = existing_classes.split()

            # Add 'exampleClass' if not already present
            if 'exampleClass' not in existing_classes:
                existing_classes.append('exampleClass')
                link_tag['class'] = existing_classes

        return str(soup)

    @hookimpl
    def renderer_process_image(
        self, image_html, image_src, image_alt, image_title, page
    ):
        """
        Sets fixed `alt` for images during markdown rendering.
        """
        soup = BeautifulSoup(image_html, 'html.parser')
        img_tag = soup.find('img')

        if img_tag:
            # Set the alt attribute to 'example alt'
            img_tag['alt'] = 'example alt'

        return str(soup)

    @hookimpl
    def renderer_process_heading(
        self,
        heading_html,
        heading_text,
        heading_level,
        heading_anchor,
        page,
    ):
        """
        Process headings during markdown rendering.
        """
        soup = BeautifulSoup(heading_html, 'html.parser')
        heading_tag = soup.find(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])

        if heading_tag:
            existing_classes = heading_tag.get('class', [])
            if isinstance(existing_classes, str):
                existing_classes = existing_classes.split()

            # Add 'exampleHeading' if not already present
            if 'exampleHeading' not in existing_classes:
                existing_classes.append('exampleHeading')
                heading_tag['class'] = existing_classes

        return str(soup)


plugin_manager.register(HtmlInjectionExample())
