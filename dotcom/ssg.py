from jinja2 import Environment, FileSystemLoader
import templates


env = Environment(loader=FileSystemLoader(next(iter(templates.__path__))))

# index
index = env.get_template("index.html")

with open("default.html", "w") as file:
    file.write(index.render(active="index"))

with open("index.html", "w") as file:
    file.write(index.render(active="index"))

# learn more
more = env.get_template("find-out-more-about-lurnby.html")
with open("find-out-more-about-lurnby.html", "w") as file:
    file.write(more.render(active="more"))

# how it works
works = env.get_template("how-lurnby-works.html")
with open("how-lurnby-works.html", "w") as file:
    file.write(works.render(active="works"))

# how much it costs
costs = env.get_template("how-much-lurnby-costs.html")
with open("how-much-lurnby-costs.html", "w") as file:
    file.write(costs.render(active="costs"))


# start using
start = env.get_template("how-to-start-using-lurnby.html")
with open("how-to-start-using-lurnby.html", "w") as file:
    file.write(start.render(active="start"))

# tutorials and demos
tutorials = env.get_template("tutorials-and-demos.html")
with open("tutorials-and-demos.html", "w") as file:
    file.write(tutorials.render(active="tutorials"))

# who is lurnby for
who = env.get_template("who-is-lurnby-for.html")
with open("who-is-lurnby-for.html", "w") as file:
    file.write(who.render(active="who"))
