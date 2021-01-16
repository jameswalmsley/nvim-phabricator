import os

from frontmatter.default_handlers import YAMLHandler
import utils
import model
import frontmatter
from pprint import pprint
from io import BytesIO, SEEK_SET
import jinja2

class Backend(object):
    def __init__(self, spath):
        self.templateLoader = jinja2.FileSystemLoader(searchpath=spath+"/templates")
        self.templateEnv = jinja2.Environment(loader=self.templateLoader)

    def update(self, task, file):
        description=""

        with open(file, 'r') as fp:
            matter = utils.parse_matter(fp)
            post = matter['frontmatter']
            description = utils.vimwiki2phab(matter['content']).strip()

            t = model.Task(None)
            t.phid = utils.phid_lookup(task)
            t.description = description

            if('title' in post):
                    t.title = post['title']
            if('points' in post):
                    t.points = post['points']
            if('assigned' in post):
                    t.assigned = post['assigned']

            if len(matter['comment']):
                    t.comment = matter['comment']

            t.commit()



    def sync(self,task, file):
        t = model.Task.fromName(task)

        template = self.templateEnv.get_template("task.md")

        post = None
        with open(file, 'r') as fp:
            post = frontmatter.load(fp)

        with open(file, 'w+') as fp:
            post.content = utils.phab2vimwiki(t.description)
            if t.assigned:
                post['assigned'] = t.assigned.username
                post['author'] = t.author.username

            if t.points:
                post['points'] = t.points

            if t.projects:
                tags = []
                projects = []
                for proj in t.projects:
                    if proj.slug:
                        tags.append(proj.slug.replace("_-_", "-"))
                    else:
                        projects.append(proj.name.replace("_-_", "-"))
                post['tags'] = tags
                post['projects'] = projects

            if t.title:
                post['title'] = t.title

            yh = YAMLHandler()
            fm = yh.export(post.metadata)

            outputText = template.render(frontmatter=fm, description=post.content.strip(), task=t, utils=utils)
            fp.write(outputText)


    def rawdiff(self, diff_name):
        phid = utils.phid_lookup(diff_name)
        r = model.Revision(phid)

        template = self.templateEnv.get_template("rawdiff.diff")
        output = template.render(r=r, utils=utils)
        print(output)
        return 0

    def create(self, title):
        tid = utils.task_create(title)
        print('T'+tid['id']+'.md')

    def approve_revision(self, diff_name):
        phid = utils.phid_lookup(diff_name)
        utils.approve_revision(phid)
