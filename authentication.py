# authentication.py
from functools import wraps
from flask import session, redirect, url_for, request

def login_required(func):
    @wraps(func)
    def wrapped(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login.login', next=request.url))
        return func(*args, **kwargs)
    return wrapped
