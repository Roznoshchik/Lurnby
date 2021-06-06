import os

import fitz
from flask_login import current_user
from werkzeug.utils import secure_filename

from app import s3, bucket


def importPDF(filepath, u=None):
    if not u:
        u = current_user
    
    doc = fitz.open(filepath)
    content = ''
    title = ''
    processed = {}

    # get all font sizes in doc
    sizes = {}
    for page in doc:
        p = page.get_text('dict')['blocks']
        for i in p:
            if i['type'] == 0:
                lines=i['lines']
                for line in lines:
                    spans = line['spans']
                    for span in spans:
                        sizes[span['size']] = span['size']
        for i in sizes:
            if i > 40:
                sizes[i] = 'h1'
            if i < 40 and i > 30:
                sizes[i] = 'h2'
            if i < 30 and i > 25:
                sizes[i] = 'h3'
            if i < 25 and i > 20:
                sizes[i] = 'h4'
            if i < 20 and i > 16:
                sizes[i] = 'h5'
            else: 
                sizes[i] = 'p'

    basedir = os.path.abspath(os.path.dirname(__file__))
    path = os.path.join(
        basedir, 'temp'
    )

    if not os.path.isdir(path):
        os.mkdir(path)

    title = doc.metadata['title']
    if title == '':
        title = doc.load_page(0).get_text()[:155] + '...'

    title_for_dir = secure_filename(title)
    path = os.path.join(
        basedir, 'temp', title_for_dir
    )

    if not os.path.isdir(path):
        os.mkdir(path) 

    img_path = os.path.join(
        path, 'images'
    )
    if not os.path.isdir(img_path):
        os.mkdir(img_path)

    az_path_base = f'{u.id}/{title_for_dir}/'
    # count for img title
    j = 0
    for page in doc:
        p = page.get_text('dict')['blocks']
        for i in p:
            # checks for images
            if i['type'] == 1:
                # if img - get extension and create filename
                # then increase count in prep for next image.
                ext = i['ext']
                file_name = f'{j}.{ext}'
                print(file_name)
                file_path = f'{img_path}/{file_name}'
                print(file_path)
                j = j + 1
                # save file to disk.
                with open(f'{file_path}', 'wb') as pic:
                    print('opened')
                    pic.write(i['image'])
                    print('saved image')
                az_path = az_path_base + file_name
                print(az_path)
                s3.upload_file(
                        Bucket = bucket,
                        Filename=file_path,
                        Key=az_path
                        )
                location = s3.get_bucket_location(Bucket=bucket)['LocationConstraint']
                # url = "https://s3-%s.amazonaws.com/%s/%s" % (location, bucket, az_path)
                url = f"/download/{u.id}/{az_path}"
                content += f'<img src ={url} loading="lazy">'
            else:
                lines = i['lines']
                font_size = None                   
                for line in lines:
                    spans = line['spans']
                    for span in spans:
                        if font_size is None:
                            font_size = span['size']
                            content += '<'
                            content += sizes[font_size]
                            content += '>'
                            content += span['text']
                        else:
                            if span['size'] == font_size:
                                content += ' '
                                content += span['text']
                            else:
                                content += '</'
                                content += sizes[font_size]
                                content += '>'
                                font_size = span['size']
                                content += '<'
                                content += sizes[font_size]
                                content += '>'
                                content += span['text']
                content += '</'
                content += sizes[font_size]
                content += '>'

    processed['content'] = content
    processed['title'] = title

    return processed
