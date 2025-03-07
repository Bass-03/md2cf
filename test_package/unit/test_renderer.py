import re

import pytest

from md2cf.confluence_renderer import ConfluenceRenderer, ConfluenceTag


def test_add_namespace():
    assert ConfluenceTag.add_namespace("tagname", "namespace") == "namespace:tagname"


def test_tag_append():
    tag = ConfluenceTag("irrelevant")
    other_tag = ConfluenceTag("alsoirrelevant")

    tag.append(other_tag)

    assert tag.children == [other_tag]


def test_tag_render():
    test_tag_type = "structured-macro"
    test_tag_markup = "<ac:structured-macro></ac:structured-macro>\n"

    tag = ConfluenceTag(test_tag_type)
    output = tag.render()

    assert output == test_tag_markup


def test_tag_render_with_text():
    test_tag_type = "structured-macro"
    test_text_content = "This is some text"
    test_tag_markup = "<ac:structured-macro>This is some text</ac:structured-macro>\n"

    tag = ConfluenceTag(test_tag_type, text=test_text_content)
    output = tag.render()

    assert output == test_tag_markup


def test_tag_render_with_cdata_text():
    test_tag_type = "structured-macro"
    test_text_content = "This is some text\nwith newlines"
    test_tag_markup = (
        "<ac:structured-macro>"
        "<![CDATA[This is some text\nwith newlines]]>"
        "</ac:structured-macro>\n"
    )

    tag = ConfluenceTag(test_tag_type, text=test_text_content, cdata=True)
    output = tag.render()

    assert output == test_tag_markup


def test_tag_render_with_attribute():
    test_tag_type = "structured-macro"
    test_tag_attrib = {"name": "code"}
    test_tag_markup = '<ac:structured-macro ac:name="code"></ac:structured-macro>\n'

    tag = ConfluenceTag(test_tag_type, attrib=test_tag_attrib)
    output = tag.render()

    assert output == test_tag_markup


def test_tag_render_with_multiple_attributes():
    test_tag_type = "structured-macro"
    test_tag_attrib = {"name": "code", "foo": "bar"}
    test_tag_markup = (
        '<ac:structured-macro ac:foo="bar" ac:name="code"></ac:structured-macro>\n'
    )

    tag = ConfluenceTag(test_tag_type, attrib=test_tag_attrib)
    output = tag.render()

    assert output == test_tag_markup


def test_tag_render_with_child():
    test_tag_type = "structured-macro"
    test_other_tag_type = "unstructured-macro"
    test_tag_markup = (
        "<ac:structured-macro>"
        "<ac:unstructured-macro>"
        "</ac:unstructured-macro>\n</ac:structured-macro>\n"
    )

    tag = ConfluenceTag(test_tag_type)
    child_tag = ConfluenceTag(test_other_tag_type)
    tag.children = [child_tag]
    output = tag.render()

    assert output == test_tag_markup


def test_tag_render_with_child_and_text():
    test_tag_type = "structured-macro"
    test_tag_text = "This is some text"
    test_other_tag_type = "unstructured-macro"
    test_tag_markup = (
        "<ac:structured-macro>"
        "<ac:unstructured-macro>"
        "</ac:unstructured-macro>\n"
        "This is some text</ac:structured-macro>\n"
    )

    tag = ConfluenceTag(test_tag_type, text=test_tag_text)
    child_tag = ConfluenceTag(test_other_tag_type)
    tag.children = [child_tag]
    output = tag.render()

    assert output == test_tag_markup


def test_renderer_reinit():
    renderer = ConfluenceRenderer()
    renderer.heading("this is a title", 1)
    assert renderer.title is not None

    renderer.reinit()
    assert renderer.title is None


def test_renderer_block_code():
    test_code = "this is a piece of code"
    test_markup = (
        '<ac:structured-macro ac:name="code">'
        '<ac:parameter ac:name="linenumbers">true</ac:parameter>\n'
        "<ac:plain-text-body><![CDATA[this is a piece of code]]></ac:plain-text-body>\n"
        "</ac:structured-macro>\n"
    )

    renderer = ConfluenceRenderer()

    assert renderer.block_code(test_code) == test_markup


def test_renderer_block_code_with_language():
    test_code = "this is a piece of code"
    test_language = "whitespace"
    test_markup = (
        '<ac:structured-macro ac:name="code">'
        '<ac:parameter ac:name="language">whitespace</ac:parameter>\n'
        '<ac:parameter ac:name="linenumbers">true</ac:parameter>\n'
        "<ac:plain-text-body><![CDATA[this is a piece of code]]></ac:plain-text-body>\n"
        "</ac:structured-macro>\n"
    )

    renderer = ConfluenceRenderer()

    assert renderer.block_code(test_code, lang=test_language) == test_markup


def test_renderer_header_sets_title():
    test_header = "this is a header"
    renderer = ConfluenceRenderer()

    renderer.heading(test_header, 1)

    assert renderer.title == test_header


def test_renderer_strips_header():
    test_header = "this is a header"
    renderer = ConfluenceRenderer(strip_header=True)

    result = renderer.heading(test_header, 1)

    assert result == ""


def test_renderer_header_lower_level_does_not_set_title():
    test_header = "this is a header"
    renderer = ConfluenceRenderer()

    renderer.heading(test_header, 2)

    assert renderer.title is None


def test_renderer_header_later_level_sets_title():
    test_lower_header = "this is a lower header"
    test_header = "this is a header"
    renderer = ConfluenceRenderer()

    renderer.heading(test_lower_header, 2)
    renderer.heading(test_header, 1)

    assert renderer.title is test_header


def test_renderer_header_only_sets_first_title():
    test_header = "this is a header"
    test_second_header = "this is another header"
    renderer = ConfluenceRenderer()

    renderer.heading(test_header, 1)
    renderer.heading(test_second_header, 1)

    assert renderer.title is test_header


def test_renderer_image_external():
    test_image_src = "http://example.com/image.jpg"
    test_image_markup = (
        '<ac:image ac:alt=""><ri:url ri:value="{}"></ri:url>\n'
        "</ac:image>\n".format(test_image_src)
    )

    renderer = ConfluenceRenderer()

    assert renderer.image(test_image_src, "", "") == test_image_markup
    assert not renderer.attachments


def test_renderer_image_external_alt_and_title():
    test_image_src = "http://example.com/image.jpg"
    test_image_alt = "alt text"
    test_image_title = "title"
    test_image_markup = (
        '<ac:image ac:alt="{}" ac:title="{}"><ri:url ri:value="{}"></ri:url>\n'
        "</ac:image>\n".format(test_image_alt, test_image_title, test_image_src)
    )

    renderer = ConfluenceRenderer()

    assert (
        renderer.image(test_image_src, test_image_title, test_image_alt)
        == test_image_markup
    )


def test_renderer_image_internal_absolute():
    test_image_file = "image.jpg"
    test_image_src = "/home/test/images/" + test_image_file
    test_image_markup = (
        '<ac:image ac:alt=""><ri:attachment ri:filename="{}"></ri:attachment>\n'
        "</ac:image>\n".format(test_image_file)
    )

    renderer = ConfluenceRenderer()

    assert renderer.image(test_image_src, "", "") == test_image_markup
    assert renderer.attachments == [test_image_src]


def test_renderer_image_internal_relative():
    test_image_file = "image.jpg"
    test_image_src = "test/images/" + test_image_file
    test_image_markup = (
        '<ac:image ac:alt=""><ri:attachment ri:filename="{}"></ri:attachment>\n'
        "</ac:image>\n".format(test_image_file)
    )

    renderer = ConfluenceRenderer()

    assert renderer.image(test_image_src, "", "") == test_image_markup
    assert renderer.attachments == [test_image_src]


def test_renderer_remove_text_newlines():
    test_text = "This is a paragraph\nwith some newlines\nin it."
    test_stripped_text = "This is a paragraph with some newlines in it."

    renderer = ConfluenceRenderer(remove_text_newlines=True)

    assert renderer.text(test_text) == test_stripped_text


@pytest.mark.parametrize("relative_links", [False, True])
def test_renderer_normal_link(relative_links):
    renderer = ConfluenceRenderer(enable_relative_links=relative_links)

    assert (
        renderer.link(url="https://example.com", text="example link", title=None)
        == '<a href="https://example.com">example link</a>'
    )


@pytest.mark.parametrize("relative_links", [False, True])
def test_renderer_local_header_link(relative_links):
    renderer = ConfluenceRenderer(enable_relative_links=relative_links)

    assert (
        renderer.link(url="#header-name", text="example link", title=None)
        == '<a href="#header-name">example link</a>'
    )


def test_renderer_relative_link_enabled():
    renderer = ConfluenceRenderer(enable_relative_links=True)

    relative_link_regex = re.compile(
        r"<a href=\"md2cf-internal-link-([-a-z0-9]+)\">relative link</a>"
    )
    temporary_link = renderer.link(
        url="document/../path/page.md", text="relative link", title=None
    )
    assert relative_link_regex.match(temporary_link)
    assert len(renderer.relative_links) == 1
    relative_link = renderer.relative_links[0]

    assert relative_link.path == "document/../path/page.md"
    assert (
        relative_link.replacement == f"md2cf-internal-link-"
        f"{relative_link_regex.match(temporary_link).groups(1)[0]}"
    )
    assert relative_link.fragment == ""
    assert relative_link.original == "document/../path/page.md"
    assert relative_link.escaped_original == "document/../path/page.md"


def test_renderer_relative_link_with_fragment_enabled():
    renderer = ConfluenceRenderer(enable_relative_links=True)

    relative_link_regex = re.compile(
        r"<a href=\"md2cf-internal-link-([-a-z0-9]+)\">relative link</a>"
    )
    temporary_link = renderer.link(
        url="document/../path/page.md#header-name", text="relative link", title=None
    )
    assert relative_link_regex.match(temporary_link)
    assert len(renderer.relative_links) == 1
    relative_link = renderer.relative_links[0]

    assert relative_link.path == "document/../path/page.md"
    assert (
        relative_link.replacement == f"md2cf-internal-link-"
        f"{relative_link_regex.match(temporary_link).groups(1)[0]}"
    )
    assert relative_link.fragment == "header-name"
    assert relative_link.original == "document/../path/page.md#header-name"
    assert relative_link.escaped_original == "document/../path/page.md#header-name"


def test_renderer_relative_link_disabled():
    renderer = ConfluenceRenderer(enable_relative_links=False)

    assert (
        renderer.link(url="document/../path/page.md", text="relative link", title=None)
        == '<a href="document/../path/page.md">relative link</a>'
    )
    assert renderer.relative_links == []


def test_renderer_relative_link_with_fragment_disabled():
    renderer = ConfluenceRenderer(enable_relative_links=False)

    assert (
        renderer.link(
            url="document/../path/page.md#header-name",
            text="relative link",
            title=None,
        )
        == '<a href="document/../path/page.md#header-name">relative link</a>'
    )
    assert renderer.relative_links == []
