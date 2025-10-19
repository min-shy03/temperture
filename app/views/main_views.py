from flask import Blueprint, render_template

from app.models import Locations

bp = Blueprint('main', __name__, url_prefix='/')

@bp.route('/')
def index():
    location_list = Locations.query.order_by(Locations.location)
    return render_template('main_page.html', location_list=location_list)