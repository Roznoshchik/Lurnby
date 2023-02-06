# set empty content
content = []
# get content and split it at the pre tag
with open("content.html", "r") as x:
    text = x.read()
    content = text.split("</pre>")
# create empty string
html = ""
for block in content:
    # each block is a pre element
    html += "<div>"  # open div
    block = block.replace("<pre>", "")  # remove old pre
    paragraphs = block.split("\n")  # split block on each new line for paragrapgs
    new_para = ""  # empty para string
    for p in paragraphs:
        new_para += f"<p>{p}</p>"  # add p tags
    block = new_para.split("<p></p>")  # split at empty paragraphs
    for b in block:
        html += f"<div>{b}</div>"  # wrap sections in divs
    html += "</div>"

content = html.split("<div></div>")  # split at empty divs

with open("newfile.html", "w") as f:
    for block in content:
        f.write(block)  # write to file
