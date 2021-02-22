import os

from flask import render_template, request
from werkzeug.utils import secure_filename

from app import s3, bucket
from app.experiments import bp
from app.experiments.ebooks import epub2text


@bp.route('/uploads', methods = ['GET', 'POST'])
def uploads():
    msg = None
    form  = request.form
    if request.method == 'POST':
        upload = request.files['file']
        if upload:
              
            filename = secure_filename(upload.filename)
            
            basedir = os.path.abspath(os.path.dirname(__file__))

            path = os.path.join(
                basedir, 'temp'
            )

            if not os.path.isdir(path):
                os.mkdir(path)

            path = os.path.join(
                basedir, 'temp', filename
            )

            upload.save(path)

            images = epub2text(path)    
            
            """
            images = get_images(path)
            for image in images:
                print (image.file_name)
                filename = str(image)
                
                s3.upload_file(
                    Bucket = bucket,
                    Filename=filename,
                    Key = filename
                )
                location = s3.get_bucket_location(Bucket=bucket)['LocationConstraint']
                url = "https://s3-%s.amazonaws.com/%s/%s" % (location, bucket, filename)

                msg = url
                break    

            
            # upload.save(filename)
            s3.upload_file(
                Bucket = bucket,
                Filename=str(images[0]),
                Key = images[0]
            )
            location = s3.get_bucket_location(Bucket=bucket)['LocationConstraint']
            url = "https://s3-%s.amazonaws.com/%s/%s" % (location, bucket, images[0])

            msg = url
            """

    return render_template('experiments/uploads.html', msg=msg)
    
    