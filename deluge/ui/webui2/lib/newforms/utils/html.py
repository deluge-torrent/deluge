"HTML utilities suitable for global use."

def escape(html):
    "Returns the given HTML with ampersands, quotes and carets encoded"
    if not isinstance(html, basestring):
        html = str(html)
    return html.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;').replace("'", '&#39;')
