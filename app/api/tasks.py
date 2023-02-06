from flask import current_app, request, url_for, jsonify
from app import CustomLogger
from app.models import Task
from app.api import bp
from app.api.auth import token_auth
from app.api.errors import bad_request, error_response
import time

logger = CustomLogger("API")


@bp.route("/tasks/<task_id>", methods=["GET"])
@token_auth.login_required
def get_task_status(task_id):
    try:
        task = Task.query.filter_by(id=task_id).first()
        if task.user_id != token_auth.current_user().id:
            return error_response(404, "resource not found")

        article_id = request.args.get("article_id", None)
        location = (
            url_for("api.get_article", article_uuid=article_id) if article_id else None
        )

        try:
            current_app.redis.ping()
        except Exception:
            logger.error("No Redis Instance")
            task.complete = True

        for _ in range(10):
            time.sleep(1)
            if task.complete:
                response = jsonify(
                    processing=False, progress=100, task_id=task_id, location=location
                )
                response.status_code = 200
                return response

        response = jsonify(
            processing=True, progress=task.get_progress(), task_id=task_id
        )
        response.status_code = 200
        return response

    except Exception as e:
        if hasattr(e, "msg"):
            return bad_request(e.msg)
        else:
            logger.error(e)
            return bad_request("Something went wrong.")
