# logout.py
from flask import Blueprint, redirect, url_for, session

logout_routes = Blueprint('logout', __name__)

@logout_routes.route('/logout', methods=['GET', 'POST'])
def logout():
    session.clear()
    return redirect(url_for('login.login'))
