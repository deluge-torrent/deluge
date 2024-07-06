#!/usr/bin/env python3
"""
Copyright © 2022-2023 Matthias Koeppe
                      Kwankyu Lee
                      Sebastian Oehms
                      Dima Pasechnik

Modified and extended for the migration of SageMath from Trac to GitHub.

Copyright © 2018-2019 Stefan Vigerske <svigerske@gams.com>

This is a modified/extended version of trac-to-gitlab from https://github.com/moimael/trac-to-gitlab.
It has been adapted to fit the needs of a specific Trac to GitLab conversion.
Then it has been adapted to fit the needs to another Trac to GitHub conversion.

Copyright © 2013 Eric van der Vlist <vdv@dyomedea.com>
                 Jens Neuhalfen <http://www.neuhalfen.name/>

This software is free software: you can redistribute it and/or modify
it under the terms of the GNU Lesser General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This sotfware is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU Lesser General Public License for more details.

You should have received a copy of the GNU Lesser General Public License
along with this library. If not, see <http://www.gnu.org/licenses/>.
"""

import re
import os
import sys
import configparser
import contextlib
import ast
import codecs
import logging
import mimetypes
import types
import gzip
import json
from urllib import parse
from collections import defaultdict
from copy import copy
from datetime import datetime
from difflib import unified_diff
from time import sleep
from roman import toRoman
from xmlrpc import client
from github import Github, GithubObject, InputFileContent
from github.Attachment import Attachment
from github.NamedUser import NamedUser
from github.Repository import Repository
from github.GithubException import IncompletableObject
from enum import Enum

# from migration_archive_writer import MigrationArchiveWritingRequester

import markdown
from markdown.extensions.tables import TableExtension

from rich.console import Console
from rich.table import Table

# import github as gh
# gh.enable_console_debug_logging()

log = logging.getLogger("trac_to_gh")

default_config = {
    "migrate": "true",
    "keywords_to_labels": "false",
    "export": "true",  # attachments
    "url": "https://api.github.com",
}

sleep_after_request = 2.0
sleep_after_attachment = 60.0
sleep_after_10tickets = 0.0  # TODO maybe this can be reduced due to the longer sleep after attaching something
sleep_before_xmlrpc = 0.33
sleep_before_xmlrpc_retry = 30.0

config = configparser.ConfigParser(default_config)
if len(sys.argv) > 1:
    config.read(sys.argv[1])
else:
    config.read("migrate.cfg")

config["source"] = {
    "url": "url",
    "keep_trac_ticket_references": True,
}
config["target"] = {
    "url": "url",
    "project_name": "project",
    "usernames": [],
    "issues_repo_url": "url",
    "git_repo_url": "url",
}
config["issues"] = {
    "migrate": False,
    "migrate_milestones": False,
}
config["attachments"] = {
    "export": False,
}
config["wiki"] = {
    "migrate": True,
    "export_dir": "export",
}

trac_url = config.get("source", "url")

cgit_url = None
if config.has_option("source", "cgit_url"):
    cgit_url = config.get("source", "cgit_url")

milestone_prefix_from = ""
if config.has_option("source", "milestone_prefix"):
    milestone_prefix_from = config.get("source", "milestone_prefix")

trac_path = None
if config.has_option("source", "path"):
    trac_path = config.get("source", "path")

keep_trac_ticket_references = config.getboolean("source", "keep_trac_ticket_references")


class subdir(Enum):
    """
    Enum for subdirectories of `trac_url_dir`
    """

    def optional_path(self):
        """
        Return the optional path for this sub directory
        according to `trac_path`
        """
        if trac_path:
            return os.path.join(trac_path, self.value)

    ticket = "ticket"
    wiki = "wiki"
    query = "query"
    report = "report"
    attachment = "attachment"
    raw_attachment = "raw-attachment"
    attachment_ticket = "attachment/ticket"
    raw_attachment_ticket = "raw-attachment/ticket"
    root = ""


class cgit_cmd(Enum):
    """
    Enum for git commands used in the cgit web interface.
    """

    commit = "commit"
    diff = "diff"
    tree = "tree"
    log = "log"
    tag = "tag"
    refs = "refs"
    plain = "plain"
    patch = "patch"
    default = ""


trac_url_dir = os.path.dirname(trac_url)
trac_url_ticket = os.path.join(trac_url_dir, subdir.ticket.value)
trac_url_wiki = os.path.join(trac_url_dir, subdir.wiki.value)
trac_url_query = os.path.join(trac_url_dir, subdir.query.value)
trac_url_report = os.path.join(trac_url_dir, subdir.report.value)
trac_url_attachment = os.path.join(trac_url_dir, subdir.attachment.value)

if config.has_option("target", "issues_repo_url"):
    target_url_issues_repo = config.get("target", "issues_repo_url")
    target_url_git_repo = config.get("target", "git_repo_url")
if config.has_option("wiki", "url"):
    target_url_wiki = config.get("wiki", "url")

github_api_url = config.get("target", "url")
github_token = None
if config.has_option("target", "token"):
    github_token = config.get("target", "token")
elif config.has_option("target", "username"):
    github_username = config.get("target", "username")
    github_password = config.get("target", "password")
else:
    github_username = None
github_project = config.get("target", "project_name")

migration_archive = None
if config.has_option("target", "migration_archive"):
    migration_archive = config.get("target", "migration_archive")

users_map = {}
user_full_names = {}
username_modules = []
if config.has_option("target", "username_modules"):
    username_modules = ast.literal_eval(config.get("target", "username_modules"))
    for module in username_modules:
        module = __import__(module)
        users_map.update(module.trac_to_github())
        user_full_names.update(module.trac_full_names())
users_map.update(ast.literal_eval(config.get("target", "usernames")))

unknown_users_prefix = ""
if config.has_option("target", "unknown_users_prefix"):
    unknown_users_prefix = config.get("target", "unknown_users_prefix")

milestone_prefix_to = ""
if config.has_option("target", "milestone_prefix"):
    milestone_prefix_to = config.get("target", "milestone_prefix")

must_convert_issues = config.getboolean("issues", "migrate")
only_issues = None
if config.has_option("issues", "only_issues"):
    only_issues = ast.literal_eval(config.get("issues", "only_issues"))
blacklist_issues = None
if config.has_option("issues", "blacklist_issues"):
    blacklist_issues = ast.literal_eval(config.get("issues", "blacklist_issues"))
filter_issues = "max=0&order=id"
if config.has_option("issues", "filter_issues"):
    filter_issues = config.get("issues", "filter_issues")
try:
    keywords_to_labels = config.getboolean("issues", "keywords_to_labels")
except ValueError:
    keywords_to_labels = ast.literal_eval(config.get("issues", "keywords_to_labels"))
migrate_milestones = config.getboolean("issues", "migrate_milestones")

milestones_to_labels = {}
if config.has_option("issues", "milestones_to_labels"):
    milestones_to_labels = ast.literal_eval(
        config.get("issues", "milestones_to_labels")
    )

canceled_milestones = {}
if config.has_option("issues", "canceled_milestones"):
    canceled_milestones = ast.literal_eval(config.get("issues", "canceled_milestones"))

components_to_labels = {}
if config.has_option("issues", "components_to_labels"):
    components_to_labels = ast.literal_eval(
        config.get("issues", "components_to_labels")
    )

add_label = None

if config.has_option("issues", "add_label"):
    add_label = config.get("issues", "add_label")

# 6-digit hex notation with leading '#' sign (e.g. #FFAABB) or one of the CSS color names
# (https://developer.mozilla.org/en-US/docs/Web/CSS/color_value#Color_keywords)
labelcolor = {
    "component": "08517b",
    "priority": "ff0000",
    "severity": "ee0000",
    "type": "008080",
    "keyword": "eeeeee",
    "milestone": "008080",
    "resolution": "008080",
}
if config.has_option("issues", "label_colors"):
    labelcolor.update(ast.literal_eval(config.get("issues", "label_colors")))

ignored_values = []
if config.has_option("issues", "ignored_values"):
    ignored_values = ast.literal_eval(config.get("issues", "ignored_values"))

ignored_names = set([])
if config.has_option("issues", "ignored_names"):
    ignored_names = set(ast.literal_eval(config.get("issues", "ignored_names")))

ignored_mentions = set([])
if config.has_option("issues", "ignored_mentions"):
    ignored_mentions = set(ast.literal_eval(config.get("issues", "ignored_mentions")))

attachment_export = config.getboolean("attachments", "export")
if attachment_export:
    attachment_export_dir = config.get("attachments", "export_dir")
    if config.has_option("attachments", "export_url"):
        attachment_export_url = config.get("attachments", "export_url")
        if not attachment_export_url.endswith("/"):
            attachment_export_url += "/"
    else:
        attachment_export_url = target_url_issues_repo
        if not attachment_export_url.endswith("/"):
            attachment_export_url += "/"
        attachment_export_url += "files/"

must_convert_wiki = config.getboolean("wiki", "migrate")
wiki_export_dir = None
if must_convert_wiki or config.has_option("wiki", "export_dir"):
    wiki_export_dir = config.get("wiki", "export_dir")

default_multilines = False
if config.has_option("source", "default_multilines"):
    # set this boolean in the source section of the configuration file
    # to change the default of the multilines flag in the function
    # trac2markdown
    default_multilines = config.getboolean("source", "default_multilines")

from diskcache import Cache

cache = Cache("trac_cache", size_limit=int(20e9))

gh_labels = dict()
gh_user = None

closing_commits = {}  # (src_ticket_id, commit) -> closing_commit


def read_closing_commits():
    # Generated using write-closing-commits.sh
    if os.path.exists("closing_commits.txt"):
        with open("closing_commits.txt", "r") as f:
            for line_number, line in enumerate(f.readlines(), start=1):
                if m := re.match(
                    "^([0-9a-f]{40}) Merge: ([0-9a-f]{40}) ([0-9a-f]{40}) Trac #([0-9]+):",
                    line,
                ):
                    sha = m.group(1)
                    parent2_sha = m.group(3)
                    src_ticket_id = int(m.group(4))
                    try:
                        other_sha = closing_commits[src_ticket_id, parent2_sha]
                    except KeyError:
                        pass
                    else:
                        log.warning(
                            f"closing_commits.txt:{line_number}: multiple commits for ticket #{src_ticket_id} {parent2_sha}: {other_sha}, {sha}"
                        )
                    closing_commits[src_ticket_id, parent2_sha] = sha
                elif line:
                    log.warning(f"closing_commits.txt:{line_number}: malformed line")


# The file wiki_path_conversion_table.txt is created if not exists. If it
# exists, the table below is constructed from the data in the file.
create_wiki_link_conversion_table = False
wiki_path_conversion_table = {}
if os.path.exists("wiki_path_conversion_table.txt"):
    with open("wiki_path_conversion_table.txt", "r") as f:
        for line in f.readlines():
            trac_wiki_path, wiki_path = line[:-1].split(" ")
            wiki_path_conversion_table[trac_wiki_path] = wiki_path
elif must_convert_wiki:
    create_wiki_link_conversion_table = True

RE_CAMELCASE1 = re.compile(r"(?<=\s)((?:[A-Z][a-z0-9]+){2,})(?=[\s\.\,\:\;\?\!])")
RE_CAMELCASE2 = re.compile(r"(?<=\s)((?:[A-Z][a-z0-9]+){2,})$")
RE_HEADING1 = re.compile(r"^(=)\s(.+)\s=\s*([\#][^\s]*)?")
RE_HEADING2 = re.compile(r"^(==)\s(.+)\s==\s*([\#][^\s]*)?")
RE_HEADING3 = re.compile(r"^(===)\s(.+)\s===\s*([\#][^\s]*)?")
RE_HEADING4 = re.compile(r"^(====)\s(.+)\s====\s*([\#][^\s]*)?")
RE_HEADING5 = re.compile(r"^(=====)\s(.+)\s=====\s*([\#][^\s]*)?")
RE_HEADING6 = re.compile(r"^(======)\s(.+)\s======\s*([\#][^\s]*)?")
RE_HEADING1a = re.compile(r"^(=)\s([^#]+)([\#][^\s]*)?")
RE_HEADING2a = re.compile(r"^(==)\s([^#]+)([\#][^\s]*)?")
RE_HEADING3a = re.compile(r"^(===)\s([^#]+)([\#][^\s]*)?")
RE_HEADING4a = re.compile(r"^(====)\s([^#]+)([\#][^\s]*)?")
RE_HEADING5a = re.compile(r"^(=====)\s([^#]+)([\#][^\s]*)?")
RE_HEADING6a = re.compile(r"^(======)\s([^#]+)([\#][^\s]*)?")
RE_SUPERSCRIPT1 = re.compile(r"\^([^\s]+?)\^")
RE_SUBSCRIPT1 = re.compile(r",,([^\s]+?),,")
RE_IMAGE1 = re.compile(r"\[\[Image\(source:([^(]+)\)\]\]")
RE_IMAGE2 = re.compile(r"\[\[Image\(([^),]+)\)\]\]")
RE_IMAGE3 = re.compile(r"\[\[Image\(([^),]+),\slink=([^(]+)\)\]\]")
RE_IMAGE4 = re.compile(r"\[\[Image\((http[^),]+),\s([^)]+)\)\]\]")
RE_IMAGE5 = re.compile(r"\[\[Image\(([^),]+),\s([^)]+)\)\]\]")
RE_IMAGE6 = re.compile(r"\[\[Image\(([^),]+),\s*([^)]+),\s*([^)]+)\)\]\]")
RE_HTTPS1 = re.compile(r"\[\[(https?://[^\s\]\|]+)\s*\|\s*(.+?)\]\]")
RE_HTTPS2 = re.compile(r"\[\[(https?://[^\]]+)\]\]")
RE_HTTPS3 = re.compile(r"\[(https?://[^\s\[\]\|]+)\s*[\s\|]\s*([^\[\]]+)\]")
RE_HTTPS4 = re.compile(r"\[(https?://[^\s\[\]\|]+)\]")
RE_TICKET_COMMENT1 = re.compile(
    r"\[\[ticket:([1-9]\d*)#comment:([1-9]\d*)\s*\|\s*(.+?)\]\]"
)
RE_TICKET_COMMENT2 = re.compile(r"\[\[ticket:([1-9]\d*)#comment:([1-9]\d*)\]\]")
RE_TICKET_COMMENT3 = re.compile(r"\[ticket:([1-9]\d*)#comment:([1-9]\d*)\s+(.*?)\]")
RE_TICKET_COMMENT4 = re.compile(r"\[ticket:([1-9]\d*)#comment:([0])\s+(.*?)\]")
RE_TICKET_COMMENT5 = re.compile(r"\[comment:ticket:([1-9]\d*):([1-9]\d*)\s+(.*?)\]")
RE_TICKET_COMMENT6 = re.compile(r"ticket:([1-9]\d*)#comment:([1-9]\d*)")
RE_COMMENT1 = re.compile(r"\[\[comment:([1-9]\d*)\]\]")
RE_COMMENT2 = re.compile(r"\[\[comment:([1-9]\d*)\s*\|\s*(.+?)\]\]")
RE_COMMENT3 = re.compile(r"\[comment:([1-9]\d*)\s+(.*?)\]")
RE_COMMENT4 = re.compile(
    r"(?<=\s)comment:([1-9]\d*)"
)  # need to exclude the string as part of http url
RE_ATTACHMENT1 = re.compile(r"\[\[attachment:([^\s\|\]]+)[\s\|](.+?)\]\]")
RE_ATTACHMENT2 = re.compile(r"\[\[attachment:([^\s]+?)\]\]")
RE_ATTACHMENT3 = re.compile(r"\[attachment:([^\s\|\]]+)[\s\|](.+?)\]")
RE_ATTACHMENT4 = re.compile(r"\[attachment:([^\s]+?)\]")
RE_ATTACHMENT5 = re.compile(r"(?<=\s)attachment:([^\s]+)\.\s")
RE_ATTACHMENT6 = re.compile(r"^attachment:([^\s]+)\.\s")
RE_ATTACHMENT7 = re.compile(r"(?<=\s)attachment:([^\s]+)")
RE_ATTACHMENT8 = re.compile(r"^attachment:([^\s]+)")
RE_LINEBREAK1 = re.compile(r"(\[\[br\]\])")
RE_LINEBREAK2 = re.compile(r"(\[\[BR\]\])")
RE_LINEBREAK3 = re.compile(r"(\\\\\s*)")
RE_WIKI1 = re.compile(r'\[\["([^\]\|]+)["]\s*([^\[\]"]+)?["]?\]\]')
RE_WIKI2 = re.compile(r"\[\[\s*([^\]|]+)[\|]([^\[\]\|]+)\]\]")
RE_WIKI3 = re.compile(r"\[\[\s*([^\]]+)\]\]")
RE_WIKI4 = re.compile(r'\[wiki:"([^\[\]\|]+)["]\s*([^\[\]"]+)?["]?\]')
RE_WIKI5 = re.compile(r"\[wiki:([^\s\[\]\|]+)\s*[\s\|]\s*([^\[\]]+)\]")
RE_WIKI6 = re.compile(r"\[wiki:([^\s\[\]]+)\]")
RE_WIKI7 = re.compile(r"\[/wiki/([^\s\[\]]+)\s+([^\[\]]+)\]")
RE_QUERY1 = re.compile(r"\[query:\?")
RE_SOURCE1 = re.compile(r"\[source:([^\s\[\]]+)\s+([^\[\]]+)\]")
RE_SOURCE2 = re.compile(r"source:([\S]+)")
RE_BOLDTEXT1 = re.compile(r"\'\'\'(.*?)\'\'\'")
RE_ITALIC1 = re.compile(r"\'\'(.*?)\'\'")
RE_ITALIC2 = re.compile(r"(?<=\s)//(.*?)//")
RE_TICKET1 = re.compile(r"[\s]%s/([1-9]\d{0,4})" % trac_url_ticket)
RE_TICKET2 = re.compile(r"\#([1-9]\d{0,4})")
RE_UNDERLINED_CODE1 = re.compile(r"(?<=\s)_([a-zA-Z_]+)_(?=[\s,)])")
RE_UNDERLINED_CODE2 = re.compile(r"(?<=\s)_([a-zA-Z_]+)_$")
RE_UNDERLINED_CODE3 = re.compile(r"^_([a-zA-Z_]+)_(?=\s)")
RE_CODE_SNIPPET = re.compile(r"(?<!`){{{(.*?)}}}(?!\})")
RE_GITHUB_MENTION1 = re.compile("(?<=\s)@([a-zA-Z][-a-zA-Z0-9._]*[a-zA-Z0-9])")
RE_GITHUB_MENTION2 = re.compile("^@([a-zA-Z][-a-zA-Z0-9._]*[a-zA-Z0-9])")
RE_RULE = re.compile(r"^[-]{4,}\s*")
RE_NO_CAMELCASE = re.compile(r"\!(([A-Z][a-z0-9]+){2,})")
RE_COLOR = re.compile(r'<span style="color: ([a-zA-Z]+)">([a-zA-Z]+)</span>')
RE_TRAC_REPORT = re.compile(r"\[report:([0-9]+)\s*(.*?)\]")
RE_COMMIT_LIST1 = re.compile(r"\|\[(.+?)\]\((.*)\)\|<code>(.*?)</code>\|")
RE_COMMIT_LIST2 = re.compile(r"\|\[(.+?)\]\((.*)\)\|`(.*?)`\|")
RE_COMMIT_LIST3 = re.compile(r"\|(.*?)\|(.*?)\|")
RE_NEW_COMMITS = re.compile(r"(?sm)(New commits:)\n((?:\|[^\n]*\|(?:\n|$))+)")
RE_LAST_NEW_COMMITS = re.compile(
    r"(?sm)(Last \d+ new commits:)\n((?:\|[^\n]*\|(?:\n|$))+)"
)


class CodeTag:
    """
    Handler for code protectors.
    """

    def replace(self, text):
        """
        Return the given string with protection tags replaced by their proper counterparts.
        """
        text = text.replace(self.tag, self._code)
        return text

    def __init__(self, tag, code):
        self.tag = tag
        self._code = code


at_sign = CodeTag("AT__SIGN__IN__CODE", "@")
linebreak_sign1 = CodeTag("LINEBREAK__SIGN1__IN__CODE", r"\\")
linebreak_sign2 = CodeTag("LINEBREAK__SIGN2__IN__CODE", r"[[br]]")
linebreak_sign3 = CodeTag("LINEBREAK__SIGN3__IN__CODE", r"[[BR]]")


class Brackets:
    """
    Handler for bracket protectors.
    """

    def replace(self, text):
        """
        Return the given string with protection tags replaced by their proper counterparts.
        """
        text = text.replace(self.open, self._open_bracket)
        text = text.replace(self.close, self._close_bracket)
        return text

    def __init__(self, open_tag, close_tag, open_bracket, close_bracket):
        self.open = open_tag
        self.close = close_tag
        self._open_bracket = open_bracket
        self._close_bracket = close_bracket


link_displ = Brackets("OPENING__LEFT__BRACKET", "CLOSING__RIGHT__BRACKET", "[", "]")
proc_code = Brackets(
    "OPENING__PROCESSOR__CODE", "CLOSING__PROCESSOR__CODE", "```", "```"
)
proc_td = Brackets(
    "OPENING__PROCESSOR__TD", "CLOSING__PROCESSOR__TD", r'<div align="left">', r"</div>"
)


class SourceUrlConversionHelper:
    """
    Conversion helper for pattern involving url-data from source configuration.
    """

    class regex(Enum):
        pass

    def __init__(self, url):
        self._re = {}
        if not url:
            # path might be optional dependend on configuration
            return
        for reg in self.regex:
            expr, path, argument = reg.value
            if isinstance(path, Enum):
                path = path.value
            if path is None:
                # path might be optional dependend on configuration
                continue
            path = os.path.join(url, path)
            self._re[reg] = re.compile(r"%s%s" % (self._url_pattern(path), expr))

    def _url_pattern(self, url):
        pattern = url.replace("https", "https?")
        pattern = pattern.replace(".", "\\.")
        return pattern

    def sub(self, text):
        if not len(self._re):
            # all expressions are optional and not activ
            return text
        for reg in self._re.keys():
            expr, path, argument = reg.value
            text = self._re[reg].sub(argument, text)
        return text


class TracUrlConversionHelper(SourceUrlConversionHelper):
    """
    Conversion helper for pattern involving the Trac url.
    """

    class regex(Enum):
        """ """

        def convert_wiki_link(match):
            trac_path = match.group(1)

            if trac_path in wiki_path_conversion_table:
                wiki_path = wiki_path_conversion_table[trac_path]
                return os.path.join(target_url_wiki, wiki_path)
            return match.group(0)

        def convert_ticket_attachment(match):
            ticket_id = match.group(1)
            filename = match.group(2)
            if keep_trac_ticket_references:
                return os.path.join(trac_url_attachment, "ticket", ticket_id, filename)
            return gh_attachment_url(ticket_id, filename)

        TICKET1 = [r"/(\d+)#comment:(\d+)?", subdir.ticket, r"ticket:\1#comment:\2"]
        TICKET2 = [
            r"/(\d+)#comment:(\d+)?",
            subdir.ticket.optional_path(),
            r"ticket:\1#comment:\2",
        ]
        TICKET3 = [r"/(\d+)", subdir.ticket, r"%s/issues/\1" % target_url_issues_repo]
        TICKET4 = [
            r"/(\d+)",
            subdir.ticket.optional_path(),
            r"%s/issues/\1" % target_url_issues_repo,
        ]
        WIKI1 = [r"/([/\-\w0-9@:%._+~#=]+)", subdir.wiki, convert_wiki_link]
        ATTACHMENT1 = [
            r"/(\d+)/([/\-\w0-9@:%._+~#=]+)",
            subdir.attachment_ticket,
            convert_ticket_attachment,
        ]
        ATTACHMENT2 = [
            r"/(\d+)/([/\-\w0-9@:%._+~#=]+)",
            subdir.attachment_ticket.optional_path(),
            convert_ticket_attachment,
        ]
        ATTACHMENT3 = [
            r"/(\d+)/([/\-\w0-9@:%._+~#=]+)",
            subdir.raw_attachment_ticket,
            convert_ticket_attachment,
        ]
        ATTACHMENT4 = [
            r"/(\d+)/([/\-\w0-9@:%._+~#=]+)",
            subdir.raw_attachment_ticket.optional_path(),
            convert_ticket_attachment,
        ]


class CgitConversionHelper(SourceUrlConversionHelper):
    """
    Conversion helper for pattern involving the cgit web interface.
    """

    class regex(Enum):
        """ """

        def convert_git_link_diff1(match):
            path = match.group(1)
            hash1 = match.group(2)
            return os.path.join(target_url_git_repo, "blob", hash1, path)

        def convert_git_link_diff2(match):
            path = match.group(1)
            hash1 = match.group(2)
            return os.path.join(target_url_git_repo, "compare", hash1 + "..." + path)

        def convert_git_link_diff3(match):
            hash1 = match.group(1)
            hash2 = match.group(2)
            return os.path.join(target_url_git_repo, "compare", hash1 + "..." + hash2)

        def convert_git_link_diff4(match):
            hash1 = match.group(1)
            return os.path.join(target_url_git_repo, "commit", hash1)

        def convert_git_link_diff5(match):
            path1 = match.group(1)
            path2 = match.group(2)
            hash1 = match.group(3)
            return os.path.join(target_url_git_repo, "compare", hash1 + "..." + path2)

        def convert_git_link_diff6(match):
            branch = match.group(1)
            path = match.group(2)
            return os.path.join(target_url_git_repo, "compare", path + "..." + branch)

        def convert_git_link_diff7(match):
            branch = match.group(1)
            return os.path.join(target_url_git_repo, "commits", branch)

        def convert_git_link_diff8(match):
            branch = match.group(1)
            return os.path.join(target_url_git_repo, "commits", branch)

        def convert_git_link_commit1(match):
            path = match.group(1)
            hash1 = match.group(2)
            return os.path.join(target_url_git_repo, "commit", hash1)

        def convert_git_link_commit3(match):
            hash1 = match.group(1)
            return os.path.join(target_url_git_repo, "commit", hash1)

        def convert_git_link_commit4(match):
            path = match.group(1)
            return os.path.join(target_url_git_repo, "commits", path)

        def convert_git_link_commit5(match):
            path = match.group(1)
            return os.path.join(target_url_git_repo, "commit", path)

        def convert_git_link_commit6(match):
            path = match.group(1)
            branch = match.group(2)
            hash1 = match.group(3)
            return os.path.join(target_url_git_repo, "compare", hash1 + "..." + branch)

        def convert_git_link_commit7(match):
            path = match.group(1)
            hash1 = match.group(2)
            return os.path.join(target_url_git_repo, "commit", hash1, path)

        def convert_git_link_tree1(match):
            path = match.group(1)
            return os.path.join(target_url_git_repo, "blob/develop", path)

        def convert_git_link_tree2(match):
            branch = match.group(1)
            return os.path.join(target_url_git_repo, "tree", branch)

        def convert_git_link_log1(match):
            path = match.group(1)
            return os.path.join(target_url_git_repo, "commits", path)

        def convert_git_link_log3(match):
            hash1 = match.group(1)
            hash2 = match.group(2)
            hash3 = match.group(3)
            return os.path.join(target_url_git_repo, "compare", hash1 + "..." + hash2)

        def convert_git_link_log4(match):
            path = match.group(1)
            hash1 = match.group(2)
            return os.path.join(
                target_url_git_repo,
                "commits",
                "develop?after="
                + hash1
                + "+0"
                + "&branch=develop"
                + "&path%5B%5D="
                + "&path%5B%5D=".join(path.split("/"))
                + "&qualified_name=refs%2Fheads%2Fdevelop",
            )

        def convert_git_link_log5(match):
            path = match.group(1)
            return os.path.join(target_url_git_repo, "commits/develop", path)

        def convert_git_link_plain(match):
            path = match.group(1)
            branch = match.group(2)
            return os.path.join(target_url_git_repo, "blob", branch, path)

        def convert_git_link_patch(match):
            hash1 = match.group(1)
            return os.path.join(target_url_git_repo, "commit", hash1 + ".patch")

        def convert_git_link(match):  # catch all missed git link
            import pdb

            pdb.set_trace()

        DIFF1 = [
            r"/([/\-\w0-9@:%._+~#=]+)\?id=([0-9a-f]+)",
            cgit_cmd.diff,
            convert_git_link_diff1,
        ]
        DIFF2 = [
            r"/?\?h=([/\-\w0-9@:%._+~#=]+)&id2=([0-9a-f]+)",
            cgit_cmd.diff,
            convert_git_link_diff2,
        ]
        DIFF3 = [
            r"/?\?id2?=([0-9a-f]+)&id=([0-9a-f]+)",
            cgit_cmd.diff,
            convert_git_link_diff3,
        ]
        DIFF4 = [r"/?\?id=([0-9a-f]+)", cgit_cmd.diff, convert_git_link_diff4]
        DIFF5 = [
            r"/?([/\-\w0-9@:%._+~#=]+)\?h=([/\-\w0-9@:%._+~#=]+)&id=([0-9a-f]+)",
            cgit_cmd.diff,
            convert_git_link_diff5,
        ]
        DIFF6 = [
            r"/?\?id2=([/\-\w0-9@:%._+~#=]+)&id=([/\-\w0-9@:%._+~#=]+)",
            cgit_cmd.diff,
            convert_git_link_diff6,
        ]
        DIFF7 = [r"/?\?h=([/\-\w0-9@:%._+~#=]+)", cgit_cmd.diff, convert_git_link_diff7]
        DIFF8 = [
            r"/?\?id=([/\-\w0-9@:%._+~#=]+)",
            cgit_cmd.diff,
            convert_git_link_diff8,
        ]

        COMMIT1 = [
            r"/?\?h=([/\-\w0-9@:%._+~#=]+)&id=([0-9a-f]+)",
            cgit_cmd.commit,
            convert_git_link_commit1,
        ]
        COMMIT2 = [
            r"id=([0-9a-f]+)",
            cgit_cmd.commit,
            convert_git_link_commit3,
        ]  # misspelled
        COMMIT3 = [r"/?\?id=([0-9a-f]+)", cgit_cmd.commit, convert_git_link_commit3]
        COMMIT4 = [
            r"/?\?h=([/\-\w0-9@:%._+~#=]+)",
            cgit_cmd.commit,
            convert_git_link_commit4,
        ]
        COMMIT5 = [
            r"/?\?id=([/\-\w0-9@:%._+~#=]+)",
            cgit_cmd.commit,
            convert_git_link_commit5,
        ]
        COMMIT6 = [
            r"/([/\-\w0-9@:%._+~#=]+)\?h=([/\-\w0-9@:%._+~#=]+)&id=([0-9a-f]+)",
            cgit_cmd.commit,
            convert_git_link_commit6,
        ]
        COMMIT7 = [
            r"/([/\-\w0-9@:%._+~#=]+)\?id=([0-9a-f]+)",
            cgit_cmd.commit,
            convert_git_link_commit7,
        ]
        COMMIT8 = [
            r"/([/\-\w0-9@:%._+~#=]+)\?h=([0-9a-f]+)",
            cgit_cmd.commit,
            convert_git_link_commit7,
        ]

        TREE1 = [r"/([/\-\w0-9@:%._+~#=]+)", cgit_cmd.tree, convert_git_link_tree1]
        TREE2 = [r"/?\?h=([/\-\w0-9@:%._+~#=]+)", cgit_cmd.tree, convert_git_link_tree2]
        TREE3 = [r"/src/?", cgit_cmd.tree, r"%s/blob/master/src" % target_url_git_repo]

        LOG1 = [r"/?\?h=([/\-\w0-9@:%._+~#=]+)", cgit_cmd.log, convert_git_link_log1]
        LOG2 = [
            r"/?\?q=([0-9a-f]+)..([0-9a-f]+)&h=([0-9a-f]+)&qt=range",
            cgit_cmd.log,
            convert_git_link_log3,
        ]
        LOG3 = [
            r"/?([/\-\w0-9@:%._+~#=]+)\?h=([0-9a-f]+)",
            cgit_cmd.log,
            convert_git_link_log4,
        ]
        LOG4 = [r"/?([/\-\w0-9@:%._+~#=]+)", cgit_cmd.log, convert_git_link_log5]

        PLAIN1 = [
            r"/([/\-\w0-9@:%._+~#=]+)\?h=([/\-\w0-9@:%._+~#=]+)",
            cgit_cmd.plain,
            convert_git_link_plain,
        ]
        PATCH1 = [r"/?\?id=([0-9a-f]+)", cgit_cmd.patch, convert_git_link_patch]
        REFS1 = [r"/?", cgit_cmd.refs, r"%s/branches" % target_url_git_repo]
        TAG1 = [
            r"/?\?id=([/\-\w0-9@:%._+~#=]+)",
            cgit_cmd.tag,
            r"%s/releases/tag/\1" % target_url_git_repo,
        ]
        DEF = [r"/(.*)", cgit_cmd.default, convert_git_link]  # catch all missed


trac_url_conv_help = TracUrlConversionHelper(trac_url_dir)
cgit_conv_help = CgitConversionHelper(cgit_url)

RE_WRONG_FORMAT1 = re.compile(r"comment:(\d+):ticket:(\d+)")
RE_REPLYING_TO = re.compile(r"Replying to \[comment:(\d+)\s([\-\w0-9@._]+)\]")
RE_REPLYING_TO_TICKET = re.compile(r"Replying to \[ticket:(\d+)\s([\-\w0-9@._]+)\]")


def inline_code_snippet(match):
    code = match.group(1)
    code = code.replace(r"@", at_sign.tag)
    code = code.replace(r"\\", linebreak_sign1.tag)
    code = code.replace(r"[[br]]", linebreak_sign2.tag)
    code = code.replace(r"[[BR]]", linebreak_sign3.tag)
    if "`" in code:
        return "<code>" + code.replace("`", r"\`") + "</code>"
    else:
        return "`" + code + "`"


def convert_replying_to(match):
    comment_id = match.group(1)
    username = match.group(2)
    name = convert_trac_username(username)
    if name:  # github username
        name = "@" + name
    else:
        name = username

    return "Replying to [comment:{} {}]".format(comment_id, name)


def convert_replying_to_ticket(match):
    ticket_id = match.group(1)
    username = match.group(2)
    name = convert_trac_username(username)
    if name:  # github username
        name = "@" + name
    else:
        name = username

    return "Replying to [ticket:{}#comment:0 {}]".format(ticket_id, name)


def commits_list(match):
    t = match.group(1) + "\n"
    t += "<table>"
    for c in match.group(2).split("\n")[2:]:  # the first two are blank header
        if not c:
            continue
        m = RE_COMMIT_LIST1.match(c)
        if m:
            commit_id = m.group(1)
            commit_url = m.group(2)
            commit_msg = m.group(3).replace("\`", "`")
            t += r'<tr><td><a href="{}"><code>{}</code></a></td><td><code>{}</code></td></tr>'.format(
                commit_url, commit_id, commit_msg
            )
        else:
            m = RE_COMMIT_LIST2.match(c)
            if m:
                commit_id = m.group(1)
                commit_url = m.group(2)
                commit_msg = m.group(3)
                t += r'<tr><td><a href="{}"><code>{}</code></a></td><td><code>{}</code></td></tr>'.format(
                    commit_url, commit_id, commit_msg
                )
            else:  # unusual format
                m = RE_COMMIT_LIST3.match(c)
                commit_id = m.group(1)
                commit_msg = m.group(2)
                t += (
                    r"<tr><td><code>{}</code></td><td><code>{}</code></td></tr>".format(
                        commit_id, commit_msg
                    )
                )
    t += "</table>\n"
    return t


def github_mention(match):
    username = match.group(1)
    github_username = convert_trac_username(username, is_mention=True)
    if github_username:
        return "@" + github_username
    return "`@`" + username


def trac2markdown(text, base_path, conv_help, multilines=default_multilines):
    # conversion of url
    text = trac_url_conv_help.sub(text)
    text = cgit_conv_help.sub(text)

    # some normalization
    text = RE_WRONG_FORMAT1.sub(r"ticket:\2#comment:\1", text)
    text = RE_REPLYING_TO.sub(convert_replying_to, text)
    text = RE_REPLYING_TO_TICKET.sub(convert_replying_to_ticket, text)

    text = re.sub("\r\n", "\n", text)
    text = re.sub(r"\swiki:([a-zA-Z]+)", r" [wiki:\1]", text)

    text = re.sub(r"\[\[TOC[^]]*\]\]", "", text)
    text = re.sub(r"(?m)\[\[PageOutline\]\]\s*\n", "", text)

    if multilines:
        text = re.sub(r"^\S[^\n]+([^=-_|])\n([^\s`*0-9#=->-_|])", r"\1 \2", text)

    def heading_replace(match):
        """
        Return the replacement for the heading
        """
        level = len(match.group(1))
        heading = match.group(2).rstrip()

        if (
            not isinstance(conv_help, IssuesConversionHelper)
            and create_wiki_link_conversion_table
        ):
            with open("wiki_path_conversion_table.txt", "a") as f:
                f.write(
                    conv_help._trac_wiki_path
                    + "#"
                    + heading.replace(" ", "")
                    + " "
                    + conv_help._wiki_path
                    + "#"
                    + heading.replace(" ", "-")
                )
                f.write("\n")

        # There might be a second item if an anchor is set.
        # We ignore this anchor since it is automatically
        # set it GitHub Markdown.
        return "#" * level + " " + heading

    a = []
    level = 0
    in_td = False
    in_code = False
    in_html = False
    in_list = False
    in_table = False
    quote_depth_decreased = False
    block = []
    table = []
    list_indents = []
    previous_line = ""
    quote_prefix = ""
    text_lines = text.split("\n") + [""]
    text_lines.reverse()
    line = True
    while text_lines:
        non_blank_previous_line = bool(line)
        line = text_lines.pop()

        # cut quote prefix
        if line.startswith(quote_prefix):
            line = line[len(quote_prefix) :]
        else:
            if in_code or in_html:  # to recover from interrupted codeblock
                text_lines.append(line)  # put it back
                text_lines.append(quote_prefix + "}}}")
                line = non_blank_previous_line
                continue

            if line:  # insert a blank line when quote depth decreased
                quote_depth_decreased = True
            quote_prefix = ""

        if not (in_code or in_html):
            # quote
            prefix = ""
            m = re.match("^((?:>\s)*>\s)", line)
            if m:
                prefix += m.group(1)
            m = re.match("^(>[>\s]*)", line[len(prefix) :])
            if m:
                prefix += m.group(1)
            quote_prefix += prefix
            if quote_depth_decreased:
                a.append(quote_prefix)
                quote_depth_decreased = False
            line = line[len(prefix) :]

        if previous_line:
            line = previous_line + line
            previous_line = ""

        line_temporary = line.lstrip()
        if line_temporary.startswith("{{{") and in_code:
            level += 1
        elif re.match(r"{{{\s*#!td", line_temporary):
            in_td = True
            in_td_level = level
            in_td_prefix = re.search("{{{", line).start()
            in_td_n = 0
            in_td_defect = 0
            line = re.sub(r"{{{\s*#!td", r"%s" % proc_td.open, line)
            level += 1
        elif re.match(r"{{{\s*#!html", line_temporary) and not (in_code or in_html):
            in_html = True
            in_html_level = level
            in_html_prefix = re.search("{{{", line).start()
            in_html_n = 0
            in_html_defect = 0
            line = re.sub(r"{{{\s*#!html", r"", line)
            level += 1
        elif re.match(r"{{{\s*#!", line_temporary) and not (
            in_code or in_html
        ):  # code: python, diff, ...
            in_code = True
            in_code_level = level
            in_code_prefix = re.search("{{{", line).start()
            in_code_n = 0
            in_code_defect = 0
            if non_blank_previous_line:
                line = "\n" + line
            line = re.sub(r"{{{\s*#!([^\s]+)", r"%s\1" % proc_code.open, line)
            level += 1
        elif line_temporary.rstrip() == "{{{" and not (in_code or in_html):
            # check dangling #!...
            next_line = text_lines.pop()
            if next_line.startswith(quote_prefix):
                m = re.match("#!([a-zA-Z]+)", next_line[len(quote_prefix) :].strip())
                if m:
                    if m.group(1) == "html":
                        text_lines.append(
                            quote_prefix + line.replace("{{{", "{{{#!html")
                        )
                        continue
                    line = line.rstrip() + m.group(1)
                else:
                    text_lines.append(next_line)
            else:
                text_lines.append(next_line)

            in_code = True
            in_code_level = level
            in_code_prefix = re.search("{{{", line).start()
            in_code_n = 0
            in_code_defect = 0
            if line_temporary.rstrip() == "{{{":
                if non_blank_previous_line:
                    line = "\n" + line
                line = line.replace("{{{", proc_code.open, 1)
            else:
                if non_blank_previous_line:
                    line = "\n" + line
                line = line.replace("{{{", proc_code.open + "\n", 1)
            level += 1
        elif line_temporary.rstrip() == "}}}":
            level -= 1
            if in_td and in_td_level == level:
                in_td = False
                in_td_prefix = 0
                if in_td_defect > 0:
                    for i in range(in_td_n):
                        prev_line = a[-i - 1]
                        a[-i - 1] = (
                            prev_line[: len(quote_prefix)]
                            + in_td_defect * " "
                            + prev_line[len(quote_prefix) :]
                        )
                line = re.sub(r"}}}", r"%s" % proc_td.close, line)
            elif in_html and in_html_level == level:
                in_html = False
                id_html_prefix = 0
                if in_html_defect > 0:
                    for i in range(in_html_n):
                        prev_line = a[-i - 1]
                        a[-i - 1] = (
                            prev_line[: len(quote_prefix)]
                            + in_html_defect * " "
                            + prev_line[len(quote_prefix) :]
                        )
                line = re.sub(r"}}}", r"", line)
            elif in_code and in_code_level == level:
                in_code = False
                in_code_prefix = 0
                if in_code_defect > 0:
                    for i in range(in_code_n):
                        prev_line = a[-i - 1]
                        a[-i - 1] = (
                            prev_line[: len(quote_prefix)]
                            + in_code_defect * " "
                            + prev_line[len(quote_prefix) :]
                        )
                line = re.sub(r"}}}", r"%s" % proc_code.close, line)
        else:
            # adjust badly indented codeblocks
            if in_td:
                if line.strip():
                    indent = re.search("[^\s]", line).start()
                    if indent < in_td_prefix:
                        in_td_defect = max(in_td_defect, in_td_prefix - indent)
                in_td_n += 1
            if in_html:
                if line.strip():
                    indent = re.search("[^\s]", line).start()
                    if indent < in_html_prefix:
                        in_html_defect = max(in_html_defect, in_html_prefix - indent)
                in_html_n += 1
            if in_code:
                if line.strip():
                    indent = re.search("[^\s]", line).start()
                    if indent < in_code_prefix:
                        in_code_defect = max(in_code_defect, in_code_prefix - indent)
                in_code_n += 1

        # CamelCase wiki link
        if not (in_code or in_html or in_td):
            new_line = ""
            depth = 0
            start = 0
            end = 0
            l = len(line)
            for i in range(l + 1):
                if i == l:
                    end = i
                elif line[i] == "[":
                    if depth == 0:
                        end = i
                    depth += 1
                elif line[i] == "]":
                    depth -= 1
                    if depth == 0:
                        start = i + 1
                        new_line += line[end:start]
                if end > start:
                    converted_part = RE_CAMELCASE1.sub(
                        conv_help.camelcase_wiki_link, line[start:end]
                    )
                    converted_part = RE_CAMELCASE2.sub(
                        conv_help.camelcase_wiki_link, converted_part
                    )
                    new_line += converted_part

                    start = end

            line = new_line

        if not (in_code or in_html):
            # heading
            line = re.sub(r"^(\s*)# ", r"\1\# ", line)  # first fix unintended heading
            line = RE_HEADING1.sub(heading_replace, line)
            line = RE_HEADING2.sub(heading_replace, line)
            line = RE_HEADING3.sub(heading_replace, line)
            line = RE_HEADING4.sub(heading_replace, line)
            line = RE_HEADING5.sub(heading_replace, line)
            line = RE_HEADING6.sub(heading_replace, line)
            line = RE_HEADING1a.sub(heading_replace, line)
            line = RE_HEADING2a.sub(heading_replace, line)
            line = RE_HEADING3a.sub(heading_replace, line)
            line = RE_HEADING4a.sub(heading_replace, line)
            line = RE_HEADING5a.sub(heading_replace, line)
            line = RE_HEADING6a.sub(heading_replace, line)

            # code surrounded by underline, mistaken as italics by github
            line = RE_UNDERLINED_CODE1.sub(r"`_\1_`", line)
            line = RE_UNDERLINED_CODE2.sub(r"`_\1_`", line)
            line = RE_UNDERLINED_CODE3.sub(r"`_\1_`", line)

            # code snippet
            line = RE_CODE_SNIPPET.sub(inline_code_snippet, line)

            line = RE_SUPERSCRIPT1.sub(r"<sup>\1</sup>", line)  # superscript ^abc^
            line = RE_SUBSCRIPT1.sub(r"<sub>\1</sub>", line)  # subscript ,,abc,,

            line = RE_QUERY1.sub(
                r"[%s?" % trac_url_query, line
            )  # preconversion to URL format
            line = RE_HTTPS1.sub(conv_help.wiki_link, line)
            line = RE_HTTPS2.sub(conv_help.wiki_link, line)  # link without display text
            line = RE_HTTPS3.sub(conv_help.wiki_link, line)
            line = RE_HTTPS4.sub(conv_help.wiki_link, line)

            line = RE_IMAGE1.sub(conv_help.image_link_under_tree, line)
            line = RE_IMAGE2.sub(conv_help.image_link, line)
            line = RE_IMAGE3.sub(conv_help.image_link, line)
            line = RE_IMAGE4.sub(r'<img src="\1" \2>', line)
            line = RE_IMAGE5.sub(conv_help.wiki_image, line)  # \2 is image width
            line = RE_IMAGE6.sub(
                conv_help.image_link, line
            )  # \2 is image width, \3 is alignment

            line = RE_TICKET_COMMENT1.sub(conv_help.ticket_comment_link, line)
            line = RE_TICKET_COMMENT2.sub(conv_help.ticket_comment_link, line)
            line = RE_TICKET_COMMENT3.sub(conv_help.ticket_comment_link, line)
            line = RE_TICKET_COMMENT4.sub(conv_help.ticket_comment_link, line)
            line = RE_TICKET_COMMENT5.sub(conv_help.ticket_comment_link, line)
            line = RE_TICKET_COMMENT6.sub(conv_help.ticket_comment_link, line)

            line = RE_COMMENT1.sub(conv_help.comment_link, line)
            line = RE_COMMENT2.sub(conv_help.comment_link, line)
            line = RE_COMMENT3.sub(conv_help.comment_link, line)
            line = RE_COMMENT4.sub(conv_help.comment_link, line)

            line = RE_ATTACHMENT1.sub(conv_help.attachment, line)
            line = RE_ATTACHMENT2.sub(conv_help.attachment, line)
            line = RE_ATTACHMENT3.sub(conv_help.attachment, line)
            line = RE_ATTACHMENT4.sub(conv_help.attachment, line)
            line = RE_ATTACHMENT5.sub(conv_help.attachment, line)
            line = RE_ATTACHMENT6.sub(conv_help.attachment, line)
            line = RE_ATTACHMENT7.sub(conv_help.attachment, line)
            line = RE_ATTACHMENT8.sub(conv_help.attachment, line)

            if in_table:
                line = RE_LINEBREAK1.sub("<br>", line)
                line = RE_LINEBREAK2.sub("<br>", line)
            else:
                line = RE_LINEBREAK1.sub("\n", line)
                line = RE_LINEBREAK2.sub("\n", line)

            line = RE_WIKI4.sub(
                conv_help.wiki_link, line
            )  # for pagenames containing whitespaces
            line = RE_WIKI5.sub(conv_help.wiki_link, line)
            line = RE_WIKI6.sub(conv_help.wiki_link, line)  # link without display text
            line = RE_WIKI7.sub(conv_help.wiki_link, line)

            line = RE_SOURCE1.sub(
                r"[\2](%s/\1)" % os.path.relpath("/tree/master/", base_path), line
            )
            line = RE_SOURCE2.sub(
                r"[\1](%s/\1)" % os.path.relpath("/tree/master/", base_path), line
            )

            line = RE_BOLDTEXT1.sub(r"**\1**", line)
            line = RE_ITALIC1.sub(r"*\1*", line)
            line = RE_ITALIC2.sub(r"*\1*", line)

            line = RE_TICKET1.sub(r" #\1", line)  # replace global ticket references
            line = RE_TICKET2.sub(conv_help.ticket_link, line)

            # to avoid unintended github mention
            line = RE_GITHUB_MENTION1.sub(github_mention, line)
            line = RE_GITHUB_MENTION2.sub(github_mention, line)

            if RE_RULE.match(line):
                if not a or not a[-1].strip():
                    line = "---"
                else:
                    line = "\n---"

            line = RE_NO_CAMELCASE.sub(
                r"\1", line
            )  # no CamelCase wiki link because of leading "!"

            # convert a trac table to a github table
            if line.startswith("||"):
                if not in_table:  # header row
                    if line.endswith("||\\"):
                        previous_line = line[:-3]
                        continue
                    elif line.endswith("|| \\"):
                        previous_line = line[:-4]
                        continue
                    # construct header separator
                    parts = line.split("||")
                    sep = []
                    for part in parts:
                        if part.startswith("="):
                            part = part[1:]
                            start = ":"
                        else:
                            start = ""
                        if part.endswith("="):
                            part = part[:-1]
                            end = ":"
                        else:
                            end = ""
                        sep.append(start + "-" * len(part) + end)
                    sep = "||".join(sep)
                    if ":" in sep:
                        line = line + "\n" + sep
                    else:  # perhaps a table without header; github table needs header
                        header = re.sub(r"[^|]", " ", sep)
                        line = header + "\n" + sep + "\n" + line
                    in_table = True
                # The wiki markup allows the alignment directives to be specified on a cell-by-cell
                # basis. This is used in many examples. AFAIK this can't be properly translated into
                # the GitHub markdown as it only allows to align statements column by column.
                line = line.replace("||=", "||")  # ignore cellwise align instructions
                line = line.replace("=||", "||")  # ignore cellwise align instructions
                line = line.replace("||", "|")

            # lists
            if in_list:
                if line.strip():
                    indent = re.search("[^\s]", line).start()
                    if indent > list_leading_spaces:
                        line = line[list_leading_spaces:]

                        # adjust slightly-malformed paragraph in list for right indent -- fingers crossed
                        indent = re.search("[^\s]", line).start()
                        if indent == 1 and list_indents[0][1] == "*":
                            line = " " + line
                        elif indent == 1 and list_indents[0][1] == "-":
                            line = " " + line
                        elif indent in [1, 2] and list_indents[0][1] not in ["*", "-"]:
                            line = (3 - indent) * " " + line

                    elif indent < list_leading_spaces:
                        in_list = False
                        list_indents = []
                    elif indent == list_leading_spaces:
                        l = line[indent:]
                        if not (
                            l.startswith("* ")
                            or l.startswith("- ")
                            or re.match("^[^\s]+\.\s", l)
                        ):
                            in_list = False
                            list_indents = []
                        else:
                            line = line[list_leading_spaces:]
            l = line.lstrip()
            if l.startswith("* ") or l.startswith("- ") or re.match("^[^\s]+\.\s", l):
                if not in_list:
                    list_leading_spaces = re.search("[^\s]", line).start()
                    line = line[list_leading_spaces:]
                    in_list = True
                indent = re.search("[^\s]", line).start()
                for i in range(len(list_indents)):
                    d, t, c = list_indents[i]
                    if indent == d:
                        if line[indent] == t:
                            c += 1
                        else:
                            t = line[indent]
                            c = 1
                        list_indents = list_indents[:i] + [(d, t, c)]
                        break
                else:
                    d = indent
                    t = line[indent]
                    c = 1
                    list_indents.append((d, t, c))

                if t in ["*", "-"]:
                    # depth = 0
                    # for dd, tt, cc in list_indents:
                    #    if tt == t:
                    #        depth += 1
                    pass
                elif t == "a":
                    line = line.replace("a", chr(ord("a") + c - 1), 1)
                elif t == "1":
                    line = line.replace("1", str(c), 1)
                elif t == "i":
                    line = line.replace("i", toRoman(c).lower(), 1)

            # take care of line break "\\", which often occurs in code snippets
            l = len(line)
            new_line = ""
            start = 0
            inline_code = False
            for i in range(l + 1):
                if i == l or line[i] == "`":
                    end = i
                    part = line[start:end]
                    if not inline_code:
                        if in_table:
                            part = RE_LINEBREAK3.sub("<br>", part)
                        else:
                            part = RE_LINEBREAK3.sub("\n", part)

                        part = RE_WIKI1.sub(conv_help.wiki_link, part)
                        part = RE_WIKI2.sub(conv_help.wiki_link, part)
                        part = RE_WIKI3.sub(conv_help.wiki_link, part)

                    new_line += part
                    start = end
                    if i < l and line[i] == "`":
                        if not inline_code:
                            inline_code = True
                        else:
                            inline_code = False
            line = new_line

        # only for table with td blocks:
        if in_table:
            if line == "|\\" or line == "| \\":  # leads td block
                block = []
                continue
            if line == "|":
                table.append("|" + "NEW__LINE".join(block) + "|")
                block = []
                continue
            if line.startswith(proc_td.open):
                if len(block) > 1:
                    block.append("|")
                block.append(line)
                continue
            if in_td:
                line = re.sub("\n", "NEW__LINE", line)
                block.append(line)
                continue
            if line.startswith(proc_td.close):
                block.append(line)
                continue
            if line.startswith("|"):
                if line.endswith("|\\"):
                    previous_line = line[:-2].replace(
                        "|", "||"
                    )  # restore to trac table row
                elif line.endswith("| \\"):
                    previous_line = line[:-3].replace(
                        "|", "||"
                    )  # restore to trac table row
                else:
                    table.append(line)
                continue

            if block:  # td block may not be terminated by "|" (or trac "||")
                table.append("|" + "NEW__LINE".join(block) + "|")
                block = []

            if table:
                table_text = "\n".join(table)
                if proc_td.open in table_text:
                    html = markdown.markdown(
                        table_text,
                        extensions=[TableExtension(use_align_attribute=True)],
                    )
                    html = proc_td.replace(html)
                else:
                    html = table_text
                line = html.replace("NEW__LINE", "\n") + "\n" + line
                table = []

            in_table = False

        for l in line.split("\n"):
            a.append(quote_prefix + l)

    a = a[:-1]
    text = "\n".join(a)

    # close unclosed codeblock
    if in_code or in_html:
        text += "\n%s" % proc_code.close

    # remove artifacts
    text = proc_code.replace(text)
    text = link_displ.replace(text)
    text = at_sign.replace(text)
    text = linebreak_sign1.replace(text)
    text = linebreak_sign2.replace(text)
    text = linebreak_sign3.replace(text)

    # Some rewritings
    text = RE_COLOR.sub(r"$\\textcolor{\1}{\\text{\2}}$", text)
    text = RE_TRAC_REPORT.sub(r"[Trac report of id \1](%s/\1)" % trac_url_report, text)
    text = RE_NEW_COMMITS.sub(commits_list, text)
    text = RE_LAST_NEW_COMMITS.sub(commits_list, text)

    text = unescape(text)

    return text


def escape(text):
    text = text.replace("comment:", "COMMENT__COLON")
    return text


def unescape(text):
    text = text.replace("COMMENT__COLON", "comment:")
    return text


class WikiConversionHelper:
    """
    A class that provides conversion methods that depend on information collected
    at startup, such as Wiki page names and configuration flags.
    """

    def __init__(self, source=None, pagenames=None, sep="/"):
        """
        The Python constructor collects all the necessary information.
        """
        if source:
            pagenames = source.wiki.getAllPages()

        pagenames_splitted = []
        for p in pagenames:
            pagenames_splitted += parse.unquote(str(p)).split(sep)
        pagenames_not_splitted = [
            parse.unquote(str(p)) for p in pagenames if p not in pagenames_splitted
        ]

        self._pagenames_splitted = pagenames_splitted
        self._pagenames_not_splitted = pagenames_not_splitted
        self._attachment_path = ""

    def set_wikipage_paths(self, pagename, sep="/"):
        """
        Set paths from the wiki pagename
        """
        pagename = parse.unquote(str(pagename))
        gh_pagename = " ".join(pagename.split(sep))
        self._attachment_path = (
            gh_pagename  #  attachment_path for the wiki_image method
        )
        self._trac_wiki_path = parse.quote(pagename)
        self._wiki_path = gh_pagename.replace(" ", "/")

        if create_wiki_link_conversion_table:
            with open("wiki_path_conversion_table.txt", "a") as f:
                f.write(self._trac_wiki_path + " " + self._wiki_path)
                f.write("\n")

    def attachment(self, match):
        filename = match.group(1)
        if len(match.groups()) >= 2:
            label = match.group(2)
        else:
            label = "attachment:" + filename

        if not re.fullmatch("[-A-Za-z0-9_.]*", filename):
            import pathlib
            from hashlib import md5

            extension = pathlib.Path(filename).suffix
            filename = md5(filename.encode("utf-8")).hexdigest() + extension
        return r"[%s](%s)" % (label, os.path.join(self._attachment_path, filename))

    def ticket_link(self, match):
        """
        Return a formatted string that replaces the match object found by re
        in the case of a Trac ticket link.
        """
        ticket = match.groups()[0]
        if keep_trac_ticket_references:
            return r"[#%s](%s/%s)" % (ticket, trac_url_ticket, ticket)
        issue = ticket
        return r"[#%s](%s/issues/%s)" % (issue, target_url_issues_repo, issue)

    def ticket_comment_link(self, match):
        """
        Return a formatted string that replaces the match object found by re
        in the case of a Trac ticket comment link.
        """
        ticket = match.group(1)
        comment = match.group(2)
        if len(match.groups()) < 3:
            label = "#{} comment:{}".format(ticket, comment)
        else:
            label = match.group(3)
        if keep_trac_ticket_references:
            return escape(
                r"[%s](%s/%s#comment:%s)" % (label, trac_url_ticket, ticket, comment)
            )
        return escape(
            r"[%s](%s/issues/%s#comment:%s)"
            % (label, target_url_issues_repo, ticket, comment)
        )

    def comment_link(self, match):
        """
        Return a formatted string that replaces the match object found by re
        in the case of a comment link.
        """
        comment = match.group(1)
        if len(match.groups()) < 2:
            label = "comment:{}".format(comment)
        else:
            label = match.group(2)
        return escape(
            r"%s%s%s(#comment%s%s)"
            % (link_displ.open, label, link_displ.close, "%3A", comment)
        )

    def image_link(self, match):
        """
        Return a formatted string that replaces the match object found by re
        in the case of a image link.
        """
        filename = match.group(1)
        if len(match.groups()) < 2:
            descr = ""
        else:
            descr = match.group(2)
        return r"!%s%s%s(%s)" % (link_displ.open, descr, link_displ.close, filename)

    def image_link_under_tree(self, match):
        """
        Return a formatted string that replaces the match object found by re
        in the case of a image link under the tree path.
        """
        mg = match.groups()
        filename = mg[0]
        path = os.path.relpath("/tree/master/")
        return r"!%s%s(%s/\1)" % (link_displ.open, link_displ.close, filename, path)

    def wiki_image(self, match):
        """
        Return a formatted string that replaces the match object found by re
        in the case of a wiki link to an attached image.
        """
        mg = match.groups()
        filename = os.path.join(self._attachment_path, mg[0])
        if len(mg) > 1:
            return r'<img src="%s" width=%s>' % (filename, mg[1])
        else:
            return r'<img src="%s">' % filename

    def protect_wiki_link(self, display, link):
        """
        Return the given string encapsuled with protection tags. These will
        be replaced at the end of conversion of a line by the brackets (see
        method `link_displ.replace`). This is needed to avoid a mixture
        with Trac wiki syntax.
        """
        return r"%s%s%s(%s)" % (link_displ.open, display, link_displ.close, link)

    def wiki_link(self, match):
        """
        Return a formatted string that replaces the match object found by re
        in the case of a link to a wiki page.
        """
        mg = match.groups()
        pagename = mg[0]
        if len(mg) > 1:
            display = mg[1]
            if not display:
                display = pagename
        else:
            display = pagename

        # take care of section references
        pagename_sect = pagename.split("#")
        pagename_ori = pagename
        if len(pagename_sect) > 1:
            pagename = pagename_sect[0]
            if not display:
                display = pagename_sect[1]

        if pagename.startswith("http"):
            link = pagename_ori.strip()
            return self.protect_wiki_link(display, link)
        elif pagename in self._pagenames_splitted:
            link = pagename_ori.replace(" ", "-")
            return self.protect_wiki_link(display, link)
        elif pagename in self._pagenames_not_splitted:
            link = pagename_ori.replace("/", " ").replace(
                " ", "-"
            )  # convert to github link
            return self.protect_wiki_link(display, link)
        else:
            # We assume that this is a
            m = re.fullmatch(r"[a-zA-Z]+[?]?", pagename)
            if m:
                macro = m.group(0)
                args = None
            else:
                m = re.fullmatch(r"([a-zA-Z]+[?]?)\((.+)\)", pagename)
                if m:
                    macro = m.group(1)
                    args = m.group(2)
                else:
                    macro = None
                    args = None
            if macro:
                display = "
                link = "%s/WikiMacros#%s-macro" % (trac_url_wiki, macro)
            else:
                return (
                    link_displ.open
                    + link_displ.open
                    + mg[0]
                    + link_displ.close
                    + link_displ.close
                )

            if args:
                args = args.replace("|", r"\|")
                return self.protect_wiki_link("%s(%s)" % (display, args), link)
            return self.protect_wiki_link(display, link)

    def camelcase_wiki_link(self, match):
        """
        Return a formatted string that replaces the match object found by re
        in the case of a link to a wiki page recognized from CamelCase.
        """
        if match.group(1) in self._pagenames_splitted:
            return self.wiki_link(match)
        return match.group(0)


class IssuesConversionHelper(WikiConversionHelper):
    """
    A class that provides conversion methods that depend on information collected
    at startup, such as Wiki page names and configuration flags.
    """

    def set_ticket_paths(self, ticket_id):
        """
        Set paths from the ticket id.
        """
        self._ticket_id = ticket_id

    def attachment(self, match):
        filename = match.group(1)
        if len(match.groups()) >= 2:
            label = match.group(2)
        else:
            label = "attachment: " + filename

        if keep_trac_ticket_references:
            url = "%s/ticket/%s/%s" % (
                trac_url_attachment,
                str(self._ticket_id),
                filename,
            )
        else:
            a, _, _ = gh_create_attachment(dest, None, filename, self._ticket_id, None)
            if a.url.endswith(".gz"):
                filename += ".gz"
            url = os.path.join(
                attachment_export_url, attachment_path(self._ticket_id, filename)
            )

        return r"[%s](%s)" % (label, url)

    def image_link(self, match):
        """
        Return a formatted string that replaces the match object found by re
        in the case of a image link.
        """
        filename = match.group(1)
        if len(match.groups()) == 1:
            descr = ""
        elif len(match.groups()) == 2:
            descr = match.group(2)
        else:
            if match.group(2).startswith("width="):
                width = match.group(2)[6:]
                alignment = match.group(3)
            elif match.group(3).startswith("width="):
                width = match.group(3)[6:]
                alignment = match.group(2)
            else:
                width = "100%"
                alignment = "center"

        if keep_trac_ticket_references:
            url = "%s/ticket/%s/%s" % (
                trac_url_attachment,
                str(self._ticket_id),
                filename,
            )
        else:
            if filename.startswith("http"):
                url = filename
            elif filename.startswith("ticket:"):
                _, ticket_id, fname = filename.split(":")
                url = os.path.join(
                    attachment_export_url, attachment_path(ticket_id, fname)
                )
            else:
                url = os.path.join(
                    attachment_export_url, attachment_path(self._ticket_id, filename)
                )

        if len(match.groups()) == 3:
            return r'<div align="%s"><img src="%s" width="%s"></div>' % (
                alignment,
                url,
                width,
            )

        return r"!%s%s%s(%s)" % (link_displ.open, descr, link_displ.close, url)

    def wiki_link(self, match):
        """
        Return a formatted string that replaces the match object found by re
        in the case of a link to a wiki page.
        """
        mg = match.groups()
        pagename = mg[0]
        if len(mg) > 1:
            display = mg[1]
            if not display:
                display = pagename
        else:
            display = pagename

        # take care of section references
        pagename_sect = pagename.split("#")
        pagename_ori = pagename
        if len(pagename_sect) > 1:
            pagename = pagename_sect[0]
            if not display:
                display = pagename_sect[1]

        if pagename.startswith("http"):
            link = pagename_ori.strip()
            return self.protect_wiki_link(display, link)
        elif pagename in self._pagenames_splitted:
            link = pagename_ori.replace(" ", "")
            if link in wiki_path_conversion_table:
                link = wiki_path_conversion_table[link]
            else:
                link = pagename_ori.replace(" ", "-")
            return self.protect_wiki_link(display, "../wiki/" + link)
        elif pagename in self._pagenames_not_splitted:
            link = pagename_ori.replace(" ", "")
            if link in wiki_path_conversion_table:
                link = wiki_path_conversion_table[link]
            else:
                link = pagename_ori.replace(" ", "-")
            return self.protect_wiki_link(display, "../wiki/" + link)
        else:
            # We assume that this is a
            m = re.fullmatch(r"[a-zA-Z]+[?]?", pagename)
            if m:
                macro = m.group(0)
                args = None
            else:
                m = re.fullmatch(r"([a-zA-Z]+[?]?)\((.+)\)", pagename)
                if m:
                    macro = m.group(1)
                    args = m.group(2)
                else:
                    macro = None
                    args = None
            if macro:
                display = "
                link = "%s/WikiMacros#%s-macro" % (trac_url_wiki, macro)
            else:
                return (
                    link_displ.open
                    + link_displ.open
                    + mg[0]
                    + link_displ.close
                    + link_displ.close
                )

            if args:
                args = args.replace("|", r"\|")
                return self.protect_wiki_link("%s(%s)" % (display, args), link)
            return self.protect_wiki_link(display, link)


def github_ref_url(ref):
    if re.fullmatch(r"[0-9a-f]{40}", ref):  # commit sha
        return f"{target_url_git_repo}/commit/{ref}"
    else:  # assume branch
        return f"{target_url_git_repo}/tree/{ref}"


def github_ref_markdown(ref):
    url = github_ref_url(ref)
    if re.fullmatch(r"[0-9a-f]{40}", ref):
        # shorten displayed commit sha and use monospace
        ref = "`" + ref[:7] + "`"
    return f"[{ref}]({url})"


def convert_xmlrpc_datetime(dt):
    # datetime.strptime(str(dt), "%Y%m%dT%X").isoformat() + "Z"
    return datetime.strptime(str(dt), "%Y%m%dT%H:%M:%S")


def convert_trac_datetime(dt):
    return datetime.strptime(str(dt), "%Y-%m-%d %H:%M:%S")


def map_tickettype(tickettype):
    "Return GitHub label corresponding to Trac ``tickettype``"
    if not tickettype:
        return None
    if tickettype == "defect":
        return "t: bug"
    if tickettype == "enhancement":
        return "t: enhancement"
    # if tickettype == 'clarification':
    #     return 'question'
    # if tickettype == 'task':
    #     return 'enhancement'
    if tickettype == "PLEASE CHANGE":
        return None
    # return tickettype.lower()
    return None


def map_resolution(resolution):
    "Return GitHub label corresponding to Trac ``resolution``"
    if resolution == "fixed":
        return None
    if not resolution:
        return None
    return "r: " + resolution


component_frequency = defaultdict(lambda: 0)


def map_component(component):
    "Return GitHub label corresponding to Trac ``component``"
    if component == "PLEASE CHANGE":
        return None
    component = component.replace("_", " ").lower()

    try:
        label = components_to_labels[component]
    except KeyError:
        # Prefix it with "c: " so that they show up as one group in the GitHub dropdown list
        label = f"c: {component}"
    component_frequency[label] += 1
    return label


default_priority = None


def map_priority(priority):
    "Return GitHub label corresponding to Trac ``priority``"
    if priority == default_priority:
        return None
    try:
        numerical_priority = 5 - [
            "trivial",
            "minor",
            "major",
            "critical",
            "blocker",
        ].index(priority)
    except ValueError:
        return priority
    return f"p: {priority} / {numerical_priority}"


default_severity = "normal"


def map_severity(severity):
    "Return GitHub label corresponding to Trac ``severity``"
    if severity == default_severity:
        return None
    return severity


def map_status(status):
    "Return a pair: (status, label)"
    status = status.lower()
    if status in ["needs_review", "needs_work", "needs_info", "positive_review"]:
        return "open", "s: " + status.replace("_", " ")
    elif status in [
        "",
        "new",
        "assigned",
        "analyzed",
        "reopened",
        "open",
        "needs_info_new",
    ]:
        return "open", None
    elif status in ["closed"]:
        return "closed", None
    else:
        log.warning("unknown ticket status: " + status)
        return "open", status.replace("_", " ")


keyword_frequency = defaultdict(lambda: 0)


def map_keywords(keywords):
    "Return a pair: (list of keywords for ticket description, list of labels)"
    keep_as_keywords = []
    labels = []
    keywords = keywords.replace(";", ",")
    has_comma = "," in keywords
    for keyword in keywords.split(","):
        keyword = keyword.strip()
        if not keyword:
            continue
        if keywords_to_labels is True:
            labels.append(keyword)
        elif (
            isinstance(keywords_to_labels, dict)
            and keyword.lower() in keywords_to_labels
        ):
            labels.append(keywords_to_labels[keyword.lower()])
        else:
            keep_as_keywords.append(keyword)
            keyword_frequency[keyword.lower()] += 1
            if not has_comma:
                # Maybe not a phrase but whitespace-separated keywords
                words = keywords.split()
                if len(words) > 1:
                    for word in words:
                        word = word.lower()
                        if (
                            isinstance(keywords_to_labels, dict)
                            and word in keywords_to_labels
                        ):
                            # Map to label but don't remove from keywords because it may be part of a phrase.
                            labels.append(keywords_to_labels[word])
                        else:
                            keyword_frequency[word] += 1

    return keep_as_keywords, labels


milestone_map = {}
unmapped_milestones = defaultdict(lambda: 0)


def map_milestone(title):
    "Return a pair: (milestone title, label)"
    if not title:
        return None, None
    title = title.lower()
    if title in milestones_to_labels.keys():
        return None, milestones_to_labels[title]
    # some normalization
    if re.match("^[0-9]", title):
        title = milestone_prefix_to + title
    if re.fullmatch("%s[1-9]" % milestone_prefix_from, title):
        title = title + ".0"
    if title in canceled_milestones.keys():
        title = canceled_milestones[title]
    return title, None


def gh_create_milestone(dest, milestone_data):
    if dest is None:
        return None

    milestone = dest.create_milestone(user=gh_user_url(dest, "git"), **milestone_data)
    sleep(sleep_after_request)
    return milestone


def gh_ensure_label(dest, labelname, label_color=None, label_category=None):
    if dest is None or labelname is None:
        return
    labelname = labelname.lower()
    if labelname in gh_labels:
        return
    if label_color is None:
        label_color = labelcolor.get(labelname)
    if label_color is None:
        label_color = labelcolor[label_category]
    log.info('Create label "%s" with color #%s' % (labelname, label_color))
    gh_label = dest.create_label(labelname, label_color)
    gh_labels[labelname] = gh_label
    sleep(sleep_after_request)


def gh_create_issue(dest, issue_data):
    if dest is None:
        return None
    if "labels" in issue_data:
        labels = [gh_labels[label.lower()] for label in issue_data.pop("labels")]
    else:
        labels = GithubObject.NotSet

    description = issue_data.pop("description")

    if github:
        description_pre = ""
        description_pre += "Original creator: " + issue_data.pop("user") + "\n\n"
        description_pre += (
            "Original creation time: " + str(issue_data.pop("created_at")) + "\n\n"
        )
        description = description_pre + description
    else:
        user_url = gh_user_url(dest, issue_data["user"])
        if user_url:
            issue_data["user"] = user_url

    ## assignee = issue_data.pop('assignee', GithubObject.NotSet)
    ## if assignee is GithubObject.NotSet:
    ##     assignees = []
    ## else:
    ##     assignees = [assignee]

    gh_issue = dest.create_issue(
        issue_data.pop("title"),
        description,
        # assignee=assignee, assignees=assignees,
        milestone=issue_data.pop("milestone", GithubObject.NotSet),
        labels=labels,
        **issue_data,
    )

    log.debug("  created issue " + str(gh_issue))
    sleep(sleep_after_request)

    return gh_issue


def attachment_path(src_ticket_id, filename):
    if not re.fullmatch("[-A-Za-z0-9_.]*", filename):
        import pathlib
        from hashlib import md5

        extension = pathlib.Path(filename).suffix
        filename = md5(filename.encode("utf-8")).hexdigest() + extension
    return "ticket" + str(src_ticket_id) + "/" + filename


def gh_attachment_url(src_ticket_id, filename):
    # Example attached to https://github.com/sagemath/trac-to-github/issues/53:
    # - https://github.com/sagemath/trac-to-github/files/10328066/test_attachment.txt
    a, local_filename, note = gh_create_attachment(
        dest, None, filename, src_ticket_id, None
    )
    return a.url


mime_type_allowed_extensions = {
    "application/pdf": [".pdf"],
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": [
        ".docx"
    ],
    "application/vnd.openxmlformats-officedocument.presentationml.presentation": [
        ".pptx"
    ],
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": [".xlsx"],
    "application/vnd.oasis.opendocument.text": [".odt", ".fodt"],
    "application/vnd.oasis.opendocument.spreadsheet": [".ods", ".fods"],
    "application/vnd.oasis.opendocument.presentation": [".odp", ".fodp"],
    "application/vnd.oasis.opendocument.graphics": [".odg", ".fodg"],
    "application/vnd.oasis.opendocument.formula": [".odf"],
    "application/vnd.ms-excel": [".csv", ".xls"],
    "application/zip": [".zip"],
    "application/x-zip-compressed": [".zip"],
    "application/gzip": [".gz", ".tgz"],
    "application/x-gzip": [".gz", ".tgz"],
    "text/plain": [".csv", ".txt", ".patch"],
    "text/x-log": [".log"],
    "text/csv": [".csv"],
    "text/comma-separated-values": [".csv"],
    "application/csv": [".csv"],
    "application/excel": [".csv"],
    "application/vnd.msexcel": [".csv"],
    "text/markdown": [".md"],
    # as attachments
    "image/gif": [".gif"],
    "image/jpeg": [".jpeg", ".jpg"],
    "image/png": [".png"],
}


def gh_create_attachment(
    dest, issue, filename, src_ticket_id, attachment=None, comment=None
):
    note = None
    if attachment_export:
        if github:
            a_path = attachment_path(src_ticket_id, filename)
            local_filename = os.path.join(attachment_export_dir, "attachments", a_path)
        else:
            match mimetypes.guess_type(filename):
                case (None, encoding):
                    mimetype = "application/octet-stream"
                case (mimetype, encoding):
                    pass
                case mimetype:
                    pass

            if filename.endswith(".log"):
                # Python thinks it's text/plain.
                mimetype = "text/x-log"
            elif filename.endswith(".gz"):
                # Python thinks that .tar.gz is application/x-tar
                mimetype = "application/gzip"

            logging.info(f"Attachment {filename=} {mimetype=}")

            allowed_extensions = mime_type_allowed_extensions.get(mimetype, [])
            if not any(filename.endswith(ext) for ext in allowed_extensions):
                mimetype = "application/octet-stream"  # which is not an allowed mime type, so will be gzipped.

            # supported types from bbs-exporter-1.5.5/lib/bbs_exporter/attachment_exporter/content_type.rb:
            if mimetype in ["image/gif", "image/jpeg", "image/png"]:
                # on GHE attachment URLs are rewritten to "/storage/user" paths, links broken.
                # so we just did everything via repository_file, not attachment
                dirname = "files"
                if issue:
                    create = issue.create_attachment
            else:
                # Cannot make it an "attachment"(?)
                if mimetype not in [
                    "text/plain",
                    "text/x-log",
                    "application/gzip",
                    "application/zip",
                ]:
                    # Here we are stricter than what mime_type_allowed_extensions allows.
                    # Replace by a gzipped file
                    if attachment:
                        attachment["attachment"] = gzip.compress(
                            attachment["attachment"]
                        )
                    filename += ".gz"
                    mimetype = "application/gzip"
                    logging.info(f"Replaced by {filename=} {mimetype=}")
                dirname = "files"
                if dest:
                    create = dest.create_repository_file
            a_path = attachment_path(src_ticket_id, filename)
            local_filename = os.path.join(migration_archive, dirname, a_path)
        if github or not attachment:

            def create(asset_name, asset_content_type, asset_url, **kwds):
                # Only create the record locally
                return Attachment(
                    dest._requester,
                    None,
                    {"url": attachment_export_url + a_path},
                    completed=True,
                )

        os.makedirs(os.path.dirname(local_filename), exist_ok=True)

        if github:
            user = None
            asset_url = None
        else:
            user = comment and gh_user_url(dest, comment["user"])
            asset_url = "tarball://root/" + dirname + "/" + a_path

        a = create(
            filename,
            mimetype,
            asset_url,
            user=user,
            created_at=comment and comment.get("created_at"),
        )
        logging.info("Attachment link %s" % a.url)

        if comment:
            if github:
                note = "Attachment [%s](%s) by %s created at %s" % (
                    filename,
                    a.url,
                    comment["user"],
                    comment["created_at"],
                )
            else:
                note = "Attachment: **[%s](%s)**" % (filename, a.url)

    elif gh_user is not None:
        if dest is None:
            return
        gistname = dest.name + " issue " + str(issue.number) + " attachment " + filename
        filecontent = InputFileContent(attachment)
        try:
            gist = gh_user.create_gist(
                False,
                {gistname: filecontent},
                "Attachment %s to issue #%d created by %s at %s"
                % (filename, issue.number, comment["user"], comment["created_at"]),
            )
            note = "Attachment [%s](%s) by %s created at %s" % (
                filename,
                gist.files[gistname].raw_url,
                comment["user"],
                comment["created_at"],
            )
        except UnicodeDecodeError:
            note = (
                "Binary attachment %s by %s created at %s lost by Trac to GitHub conversion."
                % (filename, comment["user"], comment["created_at"])
            )
            logging.warning("losing attachment", filename, "in issue", issue.number)
        sleep(sleep_after_attachment)
    else:
        note = "Attachment"
    return a, local_filename, note


minimized_issue_comments = []
local_filenames = dict()  # local_filename -> comment_id


def gh_comment_issue(
    dest, issue, comment, src_ticket_id, comment_id=None, minimize=True
):
    preamble = ""
    attachments = comment.pop("attachments", [])
    # upload attachments, if there are any
    for attachment in attachments:
        a, local_filename, note = gh_create_attachment(
            dest,
            issue,
            attachment["attachment_name"],
            src_ticket_id,
            attachment,
            comment=comment,
        )
        # write attachment data to binary file
        if local_filename in local_filenames:
            logging.warning(
                f"Overwriting attachment {local_filename} with a new version"
            )
        else:
            local_filenames[local_filename] = comment_id
        open(local_filename, "wb").write(attachment["attachment"])
        if preamble:
            preamble += "\n\n"
        preamble += note

    if not preamble and github:
        preamble = "Comment by %s created at %s" % (
            comment.pop("user"),
            comment.pop("created_at"),
        )

    note = comment.pop("note", "")
    if preamble and note:
        preamble += "\n\n"
    note = preamble + note

    if comment_id:
        if (
            note.startswith("Branch pushed to git repo;")
            or note.startswith("New commits:")
            or re.match(r"^Last \d+ new commits:", note)
        ):
            anchor = f'<div id="comment:{comment_id}"></div>\n\n'
        else:
            anchor = f'<div id="comment:{comment_id}" align="right">comment:{comment_id}</div>\n\n'
        note = anchor + note

    if dest is None:
        return

    if not github:
        user_url = gh_user_url(dest, comment["user"])
        if user_url:
            comment["user"] = user_url

    c = issue.create_comment(note, **comment)
    if minimize:
        minimized_issue_comments.append(c.url)
    sleep(sleep_after_request)


priority_labels = set(
    map_priority(priority)
    for priority in ["trivial", "minor", "major", "critical", "blocker"]
)


def normalize_labels(dest, labels):
    if "r: invalid" in labels:
        if any(
            x in labels
            for x in ["r: duplicate", "r: invalid", "r: wontfix", "r: worksforme"]
        ):
            # Remove in favor of the more specific label.
            labels.remove("r: invalid")
    if any(
        x in labels
        for x in ["r: duplicate", "r: invalid", "r: wontfix", "r: worksforme"]
    ):
        labels = sorted(set(labels).difference(priority_labels))
    return labels


def gh_update_issue_property(dest, issue, key, val, oldval=None, **kwds):
    if dest is None:
        return

    if key == "labels":
        labels = [gh_labels[label.lower()] for label in val if label]
        labels = normalize_labels(dest, labels)
        if github:
            issue.set_labels(*labels)
        else:
            oldlabels = [gh_labels[label.lower()] for label in oldval if label]
            oldlabels = normalize_labels(dest, oldlabels)
            for label in oldlabels:
                if label not in labels:
                    # https://docs.github.com/en/developers/webhooks-and-events/events/issue-event-types#unlabeled
                    issue.create_event("unlabeled", label=label, **kwds)
            for label in labels:
                if label not in oldlabels:
                    # https://docs.github.com/en/developers/webhooks-and-events/events/issue-event-types#labeled
                    issue.create_event("labeled", label=label, **kwds)
    elif key == "assignees":
        if not github:
            kwds = copy(kwds)
            kwds["subject"] = kwds.pop("actor")
            for assignee in oldval:
                if assignee not in val:
                    # https://docs.github.com/en/developers/webhooks-and-events/events/issue-event-types#unassigneeed
                    issue.create_event("unassigned", actor=assignee, **kwds)
            for assignee in val:
                if assignee not in oldval:
                    # https://docs.github.com/en/developers/webhooks-and-events/events/issue-event-types#assigned
                    issue.create_event("assigned", actor=assignee, **kwds)
    elif key == "assignee":
        if issue.assignee == val:
            return
        if issue.assignees:
            issue.remove_from_assignees(issue.assignee)
        if val is not None and val is not GithubObject.NotSet and val != "":
            issue.add_to_assignees(val)
    elif key == "state":
        if github:
            issue.edit(state=val)
        else:
            # https://docs.github.com/en/developers/webhooks-and-events/events/issue-event-types#reopened
            # https://docs.github.com/en/developers/webhooks-and-events/events/issue-event-types#closed
            issue.create_event("reopened" if val == "open" else "closed", **kwds)
    elif key == "description":
        issue.edit(body=val)
    elif key == "title":
        if github:
            issue.edit(title=val)
        else:
            issue.create_event("renamed", title_was=oldval, title_is=val, **kwds)
    elif key == "milestone":
        if github:
            issue.edit(milestone=val)
        else:
            if oldval and oldval is not GithubObject.NotSet:
                # https://docs.github.com/en/developers/webhooks-and-events/events/issue-event-types#demilestoned
                issue.create_event("demilestoned", milestone=oldval, **kwds)
            if val and val is not GithubObject.NotSet:
                # https://docs.github.com/en/developers/webhooks-and-events/events/issue-event-types#milestoned
                issue.create_event("milestoned", milestone=val, **kwds)
    else:
        raise ValueError("Unknown key " + key)

    sleep(sleep_after_request)


unmapped_users = defaultdict(lambda: 0)


def convert_trac_username(origname, is_mention=False):
    if origname in ignored_values:
        return None
    if is_mention and origname in ignored_mentions:
        return None
    if origname in ignored_names:
        return None
    origname = origname.strip("\u200b").rstrip(".")
    if origname.startswith("gh-"):
        return origname[3:]
    if origname.startswith("github/"):
        # example: https://trac.sagemath.org/ticket/17999
        return origname[7:]
    if origname.startswith("gh:"):
        # example: https://trac.sagemath.org/ticket/24876
        return origname[3:]
    try:
        gh_name = users_map[origname]
    except KeyError:
        # not a known Trac user
        assert not origname.startswith("@")
        if re.fullmatch("[-A-Za-z._0-9]+", origname):
            # heuristic pattern for valid Trac account name (not an email address or full name or junk)
            pass
        else:
            return None
        gh_name = False
    else:
        if gh_name:
            return gh_name
    # create mannequin user
    username = origname.replace(".", "-").replace("_", "-").strip("-")
    username = f"{unknown_users_prefix}{username}"
    if is_mention and not username in gh_users:
        return None
    key = (origname, gh_name is not False, is_mention, "@" + username)
    if not unmapped_users[key]:
        if is_mention:
            logging.info(f"Unmapped @ mention of {origname}")
        else:
            logging.info(f"Unmapped Trac user {origname}")
    unmapped_users[key] += 1
    return username


def gh_username(dest, origname):
    username = convert_trac_username(origname)
    if username:
        _gh_user(dest, username, origname)
        return "@" + username
    return origname


gh_users = {}


def _gh_user(dest, username, origname):
    try:
        return gh_users[username]
    except KeyError:
        headers, data = dest._requester.requestJsonAndCheck(
            "GET", f"/users/{username}", input={"name": user_full_names.get(origname)}
        )
        gh_users[username] = NamedUser(dest._requester, headers, data, completed=True)
        return gh_users[username]


def gh_user_url(dest, origname):
    if origname.startswith("@"):
        username = origname[1:]
        origname = None
    else:
        username = convert_trac_username(origname)
        if not username:
            return None
    return _gh_user(dest, username, origname).url


def gh_user_url_list(dest, orignames, ignore=["somebody", "tbd", "tdb", "tba"]):
    if not orignames:
        return []
    urls = []
    for origname in orignames.split(","):
        origname = origname.strip()
        if origname and origname not in ignore:
            url = gh_user_url(dest, origname)
            if url:
                urls.append(url)
    return urls


def gh_username_list(dest, orignames, ignore=["somebody", "tbd", "tdb", "tba"]):
    "Split and transform comma- separated lists of names"
    if not orignames:
        return ""
    names = []
    for origname in orignames.split(","):
        origname = origname.strip()
        if origname and origname not in ignore:
            name = gh_username(dest, origname)
            names.append(name)
    return ", ".join(names)


@cache.memoize(ignore=[0, "source"])
def get_all_milestones(source):
    return source.ticket.milestone.getAll()


@cache.memoize(ignore=[0, "source"])
def get_milestone(source, milestone_name):
    return source.ticket.milestone.get(milestone_name)


@cache.memoize(ignore=[0, "source"])
def get_changeLog(source, src_ticket_id):
    while True:
        try:
            if sleep_before_xmlrpc:
                sleep(sleep_before_xmlrpc)
            return source.ticket.changeLog(src_ticket_id)
        except Exception as e:
            print(e)
            print("Sleeping")
            sleep(sleep_before_xmlrpc_retry)
            print("Retrying")


@cache.memoize(ignore=[0, "source"])
def get_ticket_attachment(source, src_ticket_id, attachment_name):
    while True:
        try:
            return source.ticket.getAttachment(src_ticket_id, attachment_name)
        except Exception as e:
            print(e)
            print("Sleeping")
            sleep(sleep_before_xmlrpc_retry)
            print("Retrying")


@cache.memoize()
def get_all_tickets(filter_issues):
    call = client.MultiCall(source)
    for ticket in source.ticket.query(filter_issues):
        call.ticket.get(ticket)
    return call()


def convert_issues(source, dest, only_issues=None, blacklist_issues=None):
    conv_help = IssuesConversionHelper(source)

    if migrate_milestones:
        for milestone_name in get_all_milestones(source):
            milestone = get_milestone(source, milestone_name)
            log.debug(f"Milestone: {milestone}")
            title = milestone.pop("name")
            title, label = map_milestone(title)
            if title:
                log.info("Creating milestone " + title)
                completed = milestone.pop("completed")
                new_milestone = {
                    "description": trac2markdown(
                        milestone.pop("description"), "/milestones/", conv_help, False
                    ),
                    "title": title,
                    "state": "open" if not completed else "closed",
                }
                due = milestone.pop("due")
                if due:
                    new_milestone["due_on"] = convert_xmlrpc_datetime(due)
                if completed:
                    new_milestone["updated_at"] = convert_xmlrpc_datetime(completed)
                    new_milestone["closed_at"] = convert_xmlrpc_datetime(completed)
                if milestone:
                    log.warning(f"Discarded milestone data: {milestone}")
                milestone_map[milestone_name] = gh_create_milestone(dest, new_milestone)
                log.debug(milestone_map[milestone_name])

    nextticketid = 1
    ticketcount = 0

    for src_ticket in get_all_tickets(filter_issues):
        src_ticket_id, time_created, time_changed, src_ticket_data = src_ticket

        if only_issues and src_ticket_id not in only_issues:
            print("SKIP unwanted ticket #%s" % src_ticket_id)
            continue
        if blacklist_issues and src_ticket_id in blacklist_issues:
            print("SKIP blacklisted ticket #%s" % src_ticket_id)
            continue

        if (
            github
            and not only_issues
            and not blacklist_issues
            and not config.has_option("issues", "filter_issues")
        ):
            while nextticketid < src_ticket_id:
                print(
                    "Ticket %d missing in Trac. Generating empty one in GitHub."
                    % nextticketid
                )

                issue_data = {
                    "title": "Deleted trac ticket %d" % nextticketid,
                    "description": "Ticket %d had been deleted in the original Trac instance. This empty ticket serves as placeholder to ensure a proper 1:1 mapping of ticket ids to issue ids."
                    % nextticketid,
                    "labels": [],
                }

                issue = gh_create_issue(dest, issue_data)
                gh_update_issue_property(dest, issue, "state", "closed")

                nextticketid = nextticketid + 1

        nextticketid = nextticketid + 1
        # src_ticket_data.keys(): ['status', 'changetime', 'description', 'reporter', 'cc', 'type', 'milestone', '_ts',
        # 'component', 'owner', 'summary', 'platform', 'version', 'time', 'keywords', 'resolution']

        changelog = get_changeLog(source, src_ticket_id)

        log.info(
            'Migrating ticket #%s (%3d changes): "%s"'
            % (
                src_ticket_id,
                len(changelog),
                src_ticket_data["summary"][:50].replace('"', "'"),
            )
        )

        conv_help.set_ticket_paths(src_ticket_id)

        def attr_value(s):
            "Markup for an attribute value. Boldface if nonempty."
            if s:
                return f"**{s}**"
            return "none"

        def issue_description(src_ticket_data):
            description_pre = '<div id="comment:0"></div>\n\n'
            description_post = ""

            description_post_items = []

            depends = ""
            dependencies = src_ticket_data.pop("dependencies", "")
            other_deps = []
            for dep in dependencies.replace(";", " ").replace(",", " ").split():
                dep = dep.strip()
                if m := re.fullmatch("#?([0-9]+)", dep):
                    if depends:
                        depends += "\n"
                    # Use this phrase, used by various dependency managers:
                    # https://www.dpulls.com/
                    # https://github.com/z0al/dependent-issues
                    # https://github.com/gregsdennis/dependencies-action/pull/5
                    depends += f"Depends on #{m.group(1)}"
                elif dep:
                    # some free form remark in Dependencies
                    other_deps.append(dep)
            if other_deps:
                # put it back
                src_ticket_data["dependencies"] = dependencies
            if depends:
                description_post_items.append(depends)

            owner = gh_username_list(dest, src_ticket_data.pop("owner", None))
            if owner:
                description_post_items.append(f"Assignee: {attr_value(owner)}")

            version = src_ticket_data.pop("version", None)
            if version is not None and version != "trunk":
                description_post_items.append(f"Version: {attr_value(version)}")

            # subscribe persons in cc
            cc = src_ticket_data.pop("cc", "")
            ccstr = ""
            for person in cc.replace(";", ",").split(","):
                person = person.strip()
                if person == "":
                    continue
                person = gh_username(dest, person)
                ccstr += " " + person
            if ccstr != "":
                description_post_items.append("CC: " + ccstr)

            keywords, labels = map_keywords(src_ticket_data.pop("keywords", ""))
            if keywords:
                description_post_items.append(
                    "Keywords: " + attr_value(", ".join(keywords))
                )

            branch = src_ticket_data.pop("branch", "")
            commit = src_ticket_data.pop("commit", "")
            # These two are the same in all closed-fixed tickets. Reduce noise.
            if branch and commit:
                if branch == commit:
                    description_post_items.append(
                        "Branch/Commit: " + attr_value(github_ref_markdown(branch))
                    )
                else:
                    description_post_items.append(
                        "Branch/Commit: "
                        + attr_value(
                            github_ref_markdown(branch)
                            + " @ "
                            + github_ref_markdown(commit)
                        )
                    )
            else:
                if branch:
                    description_post_items.append(
                        f"Branch: " + attr_value(github_ref_markdown(branch))
                    )
                if commit:
                    description_post_items.append(
                        f"Commit: " + attr_value(github_ref_markdown(commit))
                    )

            description = src_ticket_data.pop("description", "")

            for field, value in src_ticket_data.items():
                if (
                    not field.startswith("_")
                    and field not in ["changetime", "time"]
                    and value
                    and value not in ignored_values
                ):
                    field = field.title().replace("_", " ")
                    description_post_items.append(f"{field}: {attr_value(value)}")

            # Sort description items
            order = [
                "depends",
                "upstream",
                "cc: ",
                "component",
                "keywords",
                "****",
                "assignee",
                "author",
                "branch",
                "commit",
                "reviewer",
                "merged",
            ]
            sort_order = [
                item[:4].lower() for item in order
            ]  # weigh only initial 4 characters

            def item_key(x):
                initial = x[:4].lower()
                try:
                    return sort_order.index(initial), initial
                except ValueError:
                    return sort_order.index("****"), initial

            description_post_items = sorted(description_post_items, key=item_key)
            description_post += "\n\n" + "\n\n".join(description_post_items)

            description_post += f"\n\n_Issue created by migration from {trac_url_ticket}/{src_ticket_id}_\n\n"

            return (
                description_pre
                + trac2markdown(description, "/issues/", conv_help, False)
                + description_post
            )

        # get original component, owner
        # src_ticket_data['component'] is the component after all changes, but for creating the issue we want the component
        # that was set when the issue was created; we should get this from the first changelog entry that changed a component
        # ... and similar for other attributes
        first_old_values = {}
        for change in changelog:
            time, author, change_type, oldvalue, newvalue, permanent = change
            if change_type not in first_old_values:
                if change_type not in [
                    "cc",
                    "comment",
                    "attachment",
                ] and not change_type.startswith("_comment"):
                    field = change_type
                    if isinstance(oldvalue, str):
                        oldvalue = oldvalue.strip()
                    first_old_values[field] = oldvalue

        # If no change changed a certain attribute, then that attribute is given by ticket data
        # (When writing migration archives, this is true unconditionally.)
        if github:
            src_ticket_data.update(first_old_values)

        # Process src_ticket_data and remove (using pop) attributes that are processed already.
        # issue_description dumps everything that has not been processed in the description.

        issue_data = {}

        def milestone_labels(src_ticket_data, status):
            labels = []
            if add_label:
                labels.append(add_label)

            component = src_ticket_data.get("component", None)
            # We do not pop the component; this is to ensure that one can search for
            # Trac components even after an outdated component label is deleted in GitHub.
            if component is not None and component.strip() != "":
                label = map_component(component)
                if label:
                    labels.append(label)
                    gh_ensure_label(dest, label, label_category="component")

            priority = src_ticket_data.pop("priority", default_priority)
            if priority != default_priority:
                label = map_priority(priority)
                labels.append(label)
                gh_ensure_label(dest, label, label_category="priority")

            severity = src_ticket_data.pop("severity", default_severity)
            if severity != default_severity:
                labels.append(severity)
                gh_ensure_label(dest, severity, label_category="severity")

            tickettype = map_tickettype(src_ticket_data.pop("type", None))
            if tickettype is not None:
                labels.append(tickettype)
                gh_ensure_label(dest, tickettype, label_category="type")

            resolution = map_resolution(src_ticket_data.pop("resolution", None))
            if resolution is not None:
                labels.append(resolution)
                gh_ensure_label(dest, resolution, label_category="resolution")

            keywords, keyword_labels = map_keywords(src_ticket_data.get("keywords", ""))
            for label in keyword_labels:
                labels.append(label)
                gh_ensure_label(dest, label, label_category="keyword")

            milestone, label = map_milestone(src_ticket_data.pop("milestone", None))
            if milestone and milestone in milestone_map:
                milestone = milestone_map[milestone]
            elif milestone:
                # Unknown milestone, put it back
                logging.warning(f'Unknown milestone "{milestone}"')
                unmapped_milestones[milestone] += 1
                src_ticket_data["milestone"] = milestone
                milestone = None
            elif label:
                labels.append(label)
                gh_ensure_label(dest, label, label_category="milestone")

            status = src_ticket_data.pop("status", status)
            issue_state, label = map_status(status)
            if label:
                labels.append(label)
                gh_ensure_label(dest, label, label_category="resolution")

            labels = normalize_labels(dest, labels)
            return milestone, labels

        def title_status(summary, status=None):
            r"""
            Decode title prefixes such as [with patch, positive review] used in early Sage tickets.

            Return (cleaned up title, status)
            """
            if m := re.match(r"^\[([A-Za-z_ ,;?]*)\] *", summary):
                phrases = m.group(1).replace(";", ",").split(",")
                keep_phrases = []
                for phrase in phrases:
                    phrase = phrase.strip()
                    if re.fullmatch(
                        r"needs review|(with )?positive review|needs work", phrase
                    ):
                        status = phrase.replace("with ", "").replace(" ", "_")
                    elif re.fullmatch(
                        r"(with)? *(new|trivial)? *(patch|bundl)e?s?|(with)? *spkg",
                        phrase,
                    ):
                        pass
                    else:
                        keep_phrases.append(phrase)
                if keep_phrases:
                    summary = "[" + ", ".join(keep_phrases) + "] " + summary[m.end(0) :]
                else:
                    summary = summary[m.end(0) :]
            if not summary:
                summary = "No title"
            return summary, status

        tmp_src_ticket_data = copy(src_ticket_data)

        title, status = title_status(tmp_src_ticket_data.pop("summary"))
        milestone, labels = milestone_labels(tmp_src_ticket_data, status)
        issue_data["title"] = title
        issue_data["labels"] = labels
        if milestone:
            issue_data["milestone"] = milestone

        if not github:
            issue_data["user"] = gh_username(dest, tmp_src_ticket_data.pop("reporter"))
            issue_data["created_at"] = convert_xmlrpc_datetime(time_created)
            issue_data["updated_at"] = convert_xmlrpc_datetime(time_changed)
            issue_data["number"] = int(src_ticket_id)
            issue_data["reactions"] = []
            assignees = gh_user_url_list(dest, tmp_src_ticket_data.pop("owner"))
            issue_data["assignees"] = assignees

            # Find closed_at
            for time, author, change_type, oldvalue, newvalue, permanent in reversed(
                changelog
            ):
                if change_type == "status":
                    state, label = map_status(newvalue)
                    if state == "closed":
                        issue_data["closed_at"] = convert_xmlrpc_datetime(time)
                    break  # on the last status change

        issue_data["description"] = issue_description(tmp_src_ticket_data)

        issue = gh_create_issue(dest, issue_data)

        def update_labels(labels, add_label, remove_label, label_category="type"):
            oldlabels = copy(labels)
            if remove_label:
                with contextlib.suppress(ValueError):
                    labels.remove(remove_label)
            if add_label:
                labels.append(add_label)
                gh_ensure_label(dest, add_label, label_category=label_category)
            labels = normalize_labels(dest, labels)
            if set(labels) != set(oldlabels):
                gh_update_issue_property(
                    dest, issue, "labels", labels, oldval=oldlabels, **event_data
                )
            return labels

        if github:
            status = src_ticket_data.pop("status")
            if status in ["closed"]:
                # sometimes a ticket is already closed at creation, so close issue
                gh_update_issue_property(dest, issue, "state", "closed")
        else:
            src_ticket_data.update(first_old_values)
            title, status = title_status(
                src_ticket_data.get("summary"), src_ticket_data.get("status")
            )
            tmp_src_ticket_data = copy(src_ticket_data)
            milestone, labels = milestone_labels(tmp_src_ticket_data, status)
            assignees = gh_user_url_list(dest, tmp_src_ticket_data.pop("owner"))

            # Create issue events for initial labels & milestone
            user_url = gh_user_url(dest, tmp_src_ticket_data.get("reporter"))
            event_data = {
                "created_at": convert_xmlrpc_datetime(time_created),
                "actor": user_url,
            }
            if milestone:
                gh_update_issue_property(
                    dest, issue, "milestone", milestone, None, **event_data
                )
            for label in labels:
                update_labels([], label, None)
            gh_update_issue_property(
                dest, issue, "assignees", assignees, oldval=[], **event_data
            )

        issue_state, label = map_status(status)
        if label and label not in labels:
            update_labels([], label, None)
        last_sha = None

        def change_status(newvalue):
            oldvalue = src_ticket_data.get("status")
            src_ticket_data["status"] = newvalue
            oldstate, oldlabel = map_status(oldvalue)
            newstate, newlabel = map_status(newvalue)
            new_labels = update_labels(labels, newlabel, oldlabel)
            if issue_state != newstate:
                if newstate == "closed" and last_sha:
                    if closing_sha := closing_commits.pop(
                        (src_ticket_id, last_sha), None
                    ):
                        ## We pop the item so that the importer does not complain about RecordNotUnique.
                        # commit_id (string) -- The SHA of the commit that referenced this issue.
                        event_data["commit_id"] = closing_sha
                        # commit_url (string) -- The GitHub REST API link to the commit that referenced this issue.
                        # event_data['commit_repository'] = target_url_git_repo
                        event_data["commit_repository"] = target_url_issues_repo
                gh_update_issue_property(dest, issue, "state", newstate, **event_data)
            return newstate, new_labels

        attachments = []
        for change in changelog:
            time, author, change_type, oldvalue, newvalue, permanent = change
            change_time = str(convert_xmlrpc_datetime(time))
            # print(change)
            log.debug(
                "  %s by %s (%s -> %s)"
                % (
                    change_type,
                    author,
                    str(oldvalue)[:40].replace("\n", " "),
                    str(newvalue)[:40].replace("\n", " "),
                )
            )
            # assert attachment is None or change_type == "comment", "an attachment must be followed by a comment"
            # if author in ['anonymous', 'Draftmen888'] :
            #     print ("  SKIPPING CHANGE BY", author)
            #     continue
            user = gh_username(dest, author)
            user_url = gh_user_url(dest, author)

            comment_data = {
                "created_at": convert_trac_datetime(change_time),
                "user": user,
                "formatter": "markdown",
            }
            event_data = {
                "created_at": convert_trac_datetime(change_time),
                "actor": user_url,
            }
            if change_type == "attachment":
                # The attachment may be described in the next comment
                attachments.append(
                    {
                        "attachment": get_ticket_attachment(
                            source, src_ticket_id, newvalue
                        ).data,
                        "attachment_name": newvalue,
                    }
                )
            elif change_type == "comment":
                # oldvalue is here either x or y.x, where x is the number of this comment and y is the number of the comment that is replied to
                m = re.fullmatch(r"([0-9]+[.])?([0-9]+)", oldvalue)
                x = m and m.group(2)
                desc = newvalue.strip()
                if not desc and not attachments:
                    # empty description and not description of attachment
                    continue
                comment_data["note"] = trac2markdown(desc, "/issues/", conv_help, False)
                comment_data["attachments"] = attachments
                attachments = []
                gh_comment_issue(
                    dest,
                    issue,
                    comment_data,
                    src_ticket_id,
                    comment_id=x,
                    minimize=False,
                )
            elif change_type.startswith("_comment"):
                # this is an old version of a comment, which has been edited later (given in previous change),
                # e.g., see http://localhost:8080/ticket/3431#comment:9 http://localhost:8080/ticket/3400#comment:14
                # we will forget about these old versions and only keep the latest one
                pass
            elif change_type == "status":
                issue_state, labels = change_status(newvalue)
            elif change_type == "resolution":
                oldresolution = map_resolution(oldvalue)
                newresolution = map_resolution(newvalue)
                labels = update_labels(
                    labels, newresolution, oldresolution, "resolution"
                )
            elif change_type == "component":
                oldlabel = map_component(oldvalue)
                newlabel = map_component(newvalue)
                labels = update_labels(labels, newlabel, oldlabel, "component")
            elif change_type == "owner":
                oldvalue = gh_user_url_list(dest, oldvalue)
                newvalue = gh_user_url_list(dest, newvalue)
                gh_update_issue_property(
                    dest, issue, "assignees", newvalue, oldval=oldvalue, **event_data
                )
                # oldvalue = gh_username_list(dest, oldvalue)
                # newvalue = gh_username_list(dest, newvalue)
                # if oldvalue and newvalue:
                #     comment_data['note'] = 'Changed assignee from ' + attr_value(oldvalue) + ' to ' + attr_value(newvalue)
                # elif newvalue:
                #     comment_data['note'] = 'Assignee: ' + attr_value(newvalue)
                # else:
                #     comment_data['note'] = 'Removed assignee ' + attr_value(oldvalue)
                # if newvalue != oldvalue:
                #     gh_comment_issue(dest, issue, comment_data, src_ticket_id)
            elif change_type == "version":
                if oldvalue != "":
                    desc = "Changed version from %s to %s." % (
                        attr_value(oldvalue),
                        attr_value(newvalue),
                    )
                else:
                    desc = "Version: " + attr_value(newvalue)
                comment_data["note"] = desc
                gh_comment_issue(dest, issue, comment_data, src_ticket_id)
            elif change_type == "milestone":
                oldmilestone, oldlabel = map_milestone(oldvalue)
                newmilestone, newlabel = map_milestone(newvalue)
                if oldmilestone and oldmilestone in milestone_map:
                    oldmilestone = milestone_map[oldmilestone]
                else:
                    if oldmilestone:
                        logging.warning(f'Ignoring unknown milestone "{oldmilestone}"')
                        unmapped_milestones[oldmilestone] += 1
                    oldmilestone = GithubObject.NotSet
                if newmilestone and newmilestone in milestone_map:
                    newmilestone = milestone_map[newmilestone]
                else:
                    if newmilestone:
                        logging.warning(f'Ignoring unknown milestone "{newmilestone}"')
                        unmapped_milestones[newmilestone] += 1
                    newmilestone = GithubObject.NotSet
                if oldmilestone != newmilestone:
                    gh_update_issue_property(
                        dest,
                        issue,
                        "milestone",
                        newmilestone,
                        oldval=oldmilestone,
                        **event_data,
                    )
                labels = update_labels(labels, newlabel, oldlabel, "milestone")
            elif change_type == "cc":
                pass  # we handle only the final list of CCs (above)
            elif change_type == "type":
                oldtype = map_tickettype(oldvalue)
                newtype = map_tickettype(newvalue)
                labels = update_labels(labels, newtype, oldtype, "type")
            elif change_type == "description":
                if github:
                    issue_data["description"] = (
                        issue_description(src_ticket_data)
                        + "\n\n(changed by "
                        + user
                        + " at "
                        + change_time
                        + ")"
                    )
                    gh_update_issue_property(
                        dest,
                        issue,
                        "description",
                        issue_data["description"],
                        **event_data,
                    )
                else:
                    body = "Description changed:\n``````diff\n"
                    old_description = trac2markdown(
                        oldvalue, "/issues/", conv_help, False
                    )
                    new_description = trac2markdown(
                        newvalue, "/issues/", conv_help, False
                    )
                    body += "\n".join(
                        unified_diff(
                            old_description.split("\n"),
                            new_description.split("\n"),
                            lineterm="",
                        )
                    )
                    body += "\n``````\n"
                    comment_data["note"] = body
                    gh_comment_issue(dest, issue, comment_data, src_ticket_id)
            elif change_type == "summary":
                oldtitle, oldstatus = title_status(oldvalue)
                title, status = title_status(newvalue)
                if title != oldtitle:
                    issue_data["title"] = title
                    gh_update_issue_property(
                        dest, issue, "title", title, oldval=oldtitle, **event_data
                    )
                if status is not None:
                    issue_state, labels = change_status(status)
            elif change_type == "priority":
                oldlabel = map_priority(oldvalue)
                newlabel = map_priority(newvalue)
                labels = update_labels(labels, newlabel, oldlabel, "priority")
            elif change_type == "severity":
                oldlabel = map_severity(oldvalue)
                newlabel = map_severity(newvalue)
                labels = update_labels(labels, newlabel, oldlabel, "severity")
            elif change_type == "keywords":
                oldlabels = copy(labels)
                oldkeywords, oldkeywordlabels = map_keywords(oldvalue)
                newkeywords, newkeywordlabels = map_keywords(newvalue)
                for label in oldkeywordlabels:
                    with contextlib.suppress(ValueError):
                        labels.remove(label)
                for label in newkeywordlabels:
                    labels.append(label)
                    gh_ensure_label(dest, label, label_category="keyword")
                if oldkeywords != newkeywords:
                    comment_data["note"] = (
                        "Changed keywords from "
                        + attr_value(", ".join(oldkeywords))
                        + " to "
                        + attr_value(", ".join(newkeywords))
                    )
                    gh_comment_issue(dest, issue, comment_data, src_ticket_id)
                if labels != oldlabels:
                    gh_update_issue_property(
                        dest, issue, "labels", labels, oldval=oldlabels, **event_data
                    )
            else:
                if oldvalue in ignored_values:
                    oldvalue = ""
                if newvalue in ignored_values:
                    newvalue = ""
                if oldvalue != newvalue:
                    if change_type in ["branch", "commit"]:
                        if oldvalue:
                            oldvalue = github_ref_markdown(oldvalue)
                        if newvalue:
                            if re.fullmatch("[0-9a-f]{40}", newvalue):
                                # Store for closing references
                                last_sha = newvalue
                            newvalue = github_ref_markdown(newvalue)
                    change_type = change_type.replace("_", " ")
                    if not oldvalue:
                        comment_data[
                            "note"
                        ] = f"{change_type.title()}: {attr_value(newvalue)}"
                    else:
                        comment_data[
                            "note"
                        ] = f"Changed {change_type} from {attr_value(oldvalue)} to {attr_value(newvalue)}"
                    gh_comment_issue(dest, issue, comment_data, src_ticket_id)

        if attachments:
            comment_data["attachments"] = attachments
            attachments = []
            gh_comment_issue(dest, issue, comment_data, src_ticket_id, minimize=False)

        ticketcount += 1
        if ticketcount % 10 == 0 and sleep_after_10tickets > 0:
            print(
                "%d tickets migrated. Waiting %d seconds to let GitHub/Trac cool down."
                % (ticketcount, sleep_after_10tickets)
            )
            sleep(sleep_after_10tickets)


def convert_wiki(source, dest):
    exclude_authors = ["trac"]

    if not os.path.isdir(wiki_export_dir):
        os.makedirs(wiki_export_dir)

    client.MultiCall(source)
    conv_help = WikiConversionHelper(source)

    if os.path.exists("links.txt"):
        os.remove("links.txt")

    for pagename in source.wiki.getAllPages():
        info = source.wiki.getPageInfo(pagename)
        if info["author"] in exclude_authors:
            continue

        page = source.wiki.getPage(pagename)
        print("Migrate Wikipage", pagename)

        # Github wiki does not have folder structure
        gh_pagename = " ".join(pagename.split("/"))

        conv_help.set_wikipage_paths(pagename)
        converted = trac2markdown(
            page, os.path.dirname("/wiki/%s" % gh_pagename), conv_help
        )

        attachments = []
        for attachment in source.wiki.listAttachments(pagename):
            print("  Attachment", attachment)
            attachmentname = os.path.basename(attachment)
            attachmentdata = source.wiki.getAttachment(attachment).data

            dirname = os.path.join(wiki_export_dir, gh_pagename)
            if not os.path.isdir(dirname):
                os.makedirs(dirname)
            # write attachment data to binary file
            open(os.path.join(dirname, attachmentname), "wb").write(attachmentdata)
            attachmenturl = gh_pagename + "/" + attachmentname

            converted = re.sub(
                r"\[attachment:%s\s([^\[\]]+)\]" % re.escape(attachmentname),
                r"[\1](%s)" % attachmenturl,
                converted,
            )

            attachments.append((attachmentname, attachmenturl))

        # add a list of attachments
        if len(attachments) > 0:
            converted += "\n---\n\nAttachments:\n"
            for name, url in attachments:
                converted += " * [" + name + "](" + url + ")\n"

        # TODO we could use the GitHub API to write into the Wiki repository of the GitHub project
        outfile = os.path.join(wiki_export_dir, gh_pagename + ".md")
        # For wiki page names with slashes
        os.makedirs(os.path.dirname(outfile), exist_ok=True)
        try:
            open(outfile, "w").write(converted)
        except UnicodeEncodeError as e:
            print("EXCEPTION:", e)
            print("  Context:", e.object[e.start - 20 : e.end + 20])
            print("  Retrying with UTF-8 encoding")
            codecs.open(outfile, "w", "utf-8").write(converted)


def output_unmapped_users(data):
    table = Table(title="Unmapped users")
    table.add_column("Username", justify="right", style="cyan", no_wrap=True)
    table.add_column("Known on Trac", justify="right", style="cyan", no_wrap=True)
    table.add_column("Mention", justify="right", style="cyan", no_wrap=True)
    table.add_column("Mannequin", justify="right", style="cyan", no_wrap=True)
    table.add_column("Frequency", style="magenta")

    for key, frequency in data:
        origname, known_on_trac, is_mention, mannequin = key
        table.add_row(
            origname, str(known_on_trac), str(is_mention), mannequin, str(frequency)
        )

    console = Console()
    console.print(table)

    # The file is created if not exists
    if not os.path.exists("unmapped_users.txt"):
        with open("unmapped_users.txt", "a") as f:
            for key, frequency in data:
                origname, known_on_trac, is_mention, mannequin = key
                f.write(
                    " ".join(
                        [
                            origname,
                            str(known_on_trac),
                            str(is_mention),
                            mannequin,
                            str(frequency),
                        ]
                    )
                    + "\n"
                )


def output_unmapped_milestones(data):
    table = Table(title="Unmapped milestones")
    table.add_column("Milestone", justify="right", style="cyan", no_wrap=True)
    table.add_column("Frequency", style="magenta")

    for key, frequency in data:
        table.add_row(key, str(frequency))

    console = Console()
    console.print(table)

    # The file is created if not exists
    if not os.path.exists("unmapped_milestones.txt"):
        with open("unmapped_milestones.txt", "a") as f:
            for key, frequency in data:
                f.write(" ".join([key, str(frequency)]) + "\n")


min_keyword_frequency_displayed = 20


def output_keyword_frequency(data):
    table = Table(title="Unmapped keyword frequency")
    table.add_column("Keyword", justify="right", style="cyan", no_wrap=True)
    table.add_column("Frequency", style="magenta")

    for key, frequency in data:
        if frequency >= min_keyword_frequency_displayed:
            table.add_row(key, str(frequency))

    console = Console()
    console.print(table)

    # The file is created if not exists
    if not os.path.exists("keyword_frequency.txt"):
        with open("keyword_frequency.txt", "a") as f:
            for key, frequency in data:
                f.write(" ".join([key, str(frequency)]) + "\n")


def output_component_frequency(data):
    table = Table(title="Component frequency")
    table.add_column("Component", justify="right", style="cyan", no_wrap=True)
    table.add_column("Frequency", style="magenta")

    for keyword, frequency in data:
        table.add_row(keyword, str(frequency))

    console = Console()
    console.print(table)

    # The file is created if not exists
    if not os.path.exists("component_frequency.txt"):
        with open("component_frequency.txt", "a") as f:
            for key, frequency in data:
                f.write(" ".join([key, str(frequency)]) + "\n")


if __name__ == "__main__":
    from rich.logging import RichHandler

    FORMAT = "%(message)s"
    logging.basicConfig(
        level="INFO", format=FORMAT, datefmt="[%X]", handlers=[RichHandler()]
    )

    source = client.ServerProxy(trac_url)

    github = None
    dest = None
    gh_user = None

    if must_convert_issues:
        if github_token is not None:
            github = Github(github_token, base_url=github_api_url)
        elif github_username is not None:
            github = Github(github_username, github_password, base_url=github_api_url)
        if github:
            dest = github.get_repo(github_project)
            gh_user = github.get_user()
            for l in dest.get_labels():
                gh_labels[l.name.lower()] = l
            # print 'Existing labels:', gh_labels.keys()
        else:
            requester = MigrationArchiveWritingRequester(
                migration_archive, wiki_export_dir
            )
            dest = Repository(
                requester,
                None,
                dict(name=github_project, url=target_url_issues_repo),
                None,
            )
            # print(dest.url)
            sleep_after_request = 0

    try:
        if must_convert_issues:
            read_closing_commits()
            convert_issues(
                source, dest, only_issues=only_issues, blacklist_issues=blacklist_issues
            )

        if must_convert_wiki:
            convert_wiki(source, dest)
    finally:
        if must_convert_issues and not github:
            # Patch in labels
            dest._requester.requestJsonAndCheck(
                "PATCH",
                f"{dest.url}",
                input={
                    "labels": [
                        {
                            "url": label.url,
                            "name": label.name,
                            "color": label.color,
                            "description": label.description
                            if label.description is not GithubObject.NotSet
                            else None,
                            "created_at": None,
                        }
                        for label in gh_labels.values()
                    ]
                },
            )
            dest._requester.flush()
            with open("minimized_issue_comments.json", "w") as f:
                json.dump(minimized_issue_comments, f, indent=4)

        output_unmapped_users(
            sorted(unmapped_users.items(), key=lambda x: (x[0][0].lower(), *x[0][1:]))
        )
        output_unmapped_milestones(
            sorted(unmapped_milestones.items(), key=lambda x: -x[1])
        )
        output_keyword_frequency(sorted(keyword_frequency.items(), key=lambda x: -x[1]))
        output_component_frequency(
            sorted(component_frequency.items(), key=lambda x: -x[1])
        )
