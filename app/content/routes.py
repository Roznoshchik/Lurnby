from flask import (flash, redirect, url_for, render_template, request,
                   current_app)

from app.content import bp


@bp.route('/terms-of-service', methods=['GET'])
def terms():
    return render_template('legal/tos.html')

@bp.route('/privacy-policy', methods=['GET'])
def privacy():
    return render_template('legal/privacy.html')

@bp.route('/intellectual-property-policy', methods=['GET'])
def ipp():
    return render_template('legal/ipp.html')