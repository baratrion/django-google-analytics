from django.db import models
from django.contrib.sites.models import Site
from django.template import Library, TemplateSyntaxError, Node, loader
from django.utils.translation import ugettext as _


register = Library()


def do_get_analytics(parser, token):
    """
    Usage:

        {% analytics %}
        or
        {% analytics "UA-xxxxxx-x" %}

    Extended usage for asyncronous tracking:

        {% analytics async %}
        or
        {% analytics "UA-xxxxxx-x" async %}

    """
    bits = token.contents.split()

    if not (len(bits) >= 1 and len(bits) <= 3):
        raise TemplateSyntaxError(_("%s tag got invalid number of arguments") % bits[0])

    code = None
    async = False

    if len(bits) == 2:
        if bits[1] == 'async':
            async = True
        else:
            code = bits[1]
    if len(bits) == 3:
        if bits[2] != 'async':
            raise TemplateSyntaxError(_("if given, second argument to %s tag must be 'async'") % bits[0])
        code = bits[1]
        async = True

    if not code:
        current_site = Site.objects.get_current()
    else:
        if not (code[0] == code[-1] and code[0] in ('"', "'")):
            raise TemplateSyntaxError(_("%s tag's analytics code should be in quotes") % bits[0])
        code = code[1:-1]
        current_site = None

    return AnalyticsNode(current_site, code, async)


class AnalyticsNode(Node):
    def __init__(self, site=None, code=None, async=False):
        self.site = site
        self.code = code
        self.async = async

    def render(self, context):
        if self.site:
            code_set = self.site.analytics_set.all()
            if code_set:
                code = code_set[0].analytics_code
            else:
                return ''
        elif self.code:
            code = self.code
        else:
            return ''

        template = 'google_analytics/analytics_template.html'

        if self.async:
            template = 'google_analytics/analytics_template_async.html'

        return loader.render_to_string(template, {'analytics_code': code})

register.tag('analytics', do_get_analytics)
